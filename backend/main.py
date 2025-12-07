from fastapi import FastAPI, HTTPException, BackgroundTasks
import concurrent.futures
import threading

from models import SearchRequest, TaskCreatedResponse, TaskStatusResponse, TaskStatus
from tasks import task_manager
from query_transformer import transform_user_query
from scraper import scrape_google_products_streaming
from ranker import score_product

tags_metadata = [
    {
        "name": "Search",
        "description": "Operations for managing product search tasks. Start searches and retrieve results.",
    },
    {
        "name": "Health",
        "description": "API health monitoring endpoints.",
    },
]

app = FastAPI(
    title="Product Search API",
    description="""
## Product Search Task Management API

This API allows you to search for products asynchronously.

### How it works:

1. **Start a search** - Submit a search query and receive a task ID
2. **Poll for results** - Use the task ID to check the status
3. **Get results** - When completed, product URLs included

### Task Statuses:
- `pending` - Task created, waiting to start
- `running` - Search in progress
- `completed` - Search finished, results available
- `failed` - Search failed, error message available
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def run_search_task(task_id: str, query: str, country: str = "US"):
    """
    Background task that performs the actual product search pipeline.
    
    Pipeline (Streaming):
    1. Transform user query → Google search query + features
    2. Scrape products and rank them IN PARALLEL as they arrive
    """
    try:
        # Update task status to running
        task_manager.update_task_status(task_id, TaskStatus.RUNNING)
        task_manager.update_task_progress(
            task_id,
            current_step="transforming",
            step_message="🔍 Analyzing your search query...",
            progress_percent=5
        )

        # Step 1: Transform user query into structured search data
        print(f"[Task {task_id}] Step 1: Transforming user query...")
        search_data = transform_user_query(query)
        print(f"[Task {task_id}] ✓ Google Query: {search_data.google_search_query}")
        print(f"[Task {task_id}] ✓ Features: {search_data.product_features}")
        print(f"[Task {task_id}] ✓ Category: {search_data.product_category}")
        
        task_manager.update_task_progress(
            task_id,
            current_step="scraping",
            step_message="🏪 Searching local businesses and online stores...",
            progress_percent=10
        )

        # Step 2 & 3: Stream scraping and ranking in parallel
        print(f"[Task {task_id}] Step 2+3: Streaming scrape & rank...")
        
        # Shared state for tracking progress
        scored_products = []
        rank_futures = []
        products_scraped = 0
        products_scored = 0
        total_products = 20  # Will be updated when we know actual count
        lock = threading.Lock()
        
        # Create ranking executor that stays open during scraping
        rank_executor = concurrent.futures.ThreadPoolExecutor(max_workers=8)
        
        # Queue for completed ranking futures - allows streaming during scraping
        from queue import Queue
        done_queue = Queue()
        scraping_done = threading.Event()
        
        def on_product_scraped(product):
            """Called immediately when a product is scraped - submits it for ranking."""
            nonlocal products_scraped
            with lock:
                products_scraped += 1
                current_scraped = products_scraped
            
            print(f"[Task {task_id}] Scraped {current_scraped}: {product.get('name', 'Unknown')[:40]}")
            
            # Update progress - scraping phase is 10-40%
            progress = 10 + int((current_scraped / total_products) * 30)
            task_manager.update_task_progress(
                task_id,
                current_step="scraping",
                step_message=f"🔎 Found {current_scraped} products, analyzing...",
                total_products=current_scraped,
                progress_percent=progress
            )
            
            # Submit to ranking immediately and add callback for when done
            future = rank_executor.submit(score_product, product, query)
            future.add_done_callback(lambda f: done_queue.put(f))
            with lock:
                rank_futures.append(future)
        
        def ranking_monitor():
            """Monitor thread: streams ranked products to UI as they complete."""
            nonlocal products_scored
            while True:
                try:
                    # Wait for a completed future (with timeout to check if done)
                    future = done_queue.get(timeout=0.5)
                    try:
                        scored_product = future.result()
                        with lock:
                            scored_products.append(scored_product)
                            products_scored += 1
                            current_scored = products_scored
                            total_to_rank = len(rank_futures)
                        
                        # Update progress - ranking phase is 40-95%
                        progress = 40 + int((current_scored / max(total_to_rank, 1)) * 55)
                        task_manager.update_task_progress(
                            task_id,
                            current_step="ranking",
                            step_message=f"✨ Analyzed {current_scored} of {total_to_rank} products",
                            scored_product=scored_product,
                            progress_percent=progress
                        )
                        print(f"[Task {task_id}] Scored {current_scored}: {scored_product.get('name', 'Unknown')[:30]}")
                        
                    except Exception as e:
                        print(f"[Task {task_id}] Ranking error: {e}")
                        
                except:
                    # Timeout - check if we're done
                    with lock:
                        all_done = scraping_done.is_set() and products_scored >= len(rank_futures)
                    if all_done and done_queue.empty():
                        break
        
        # Start ranking monitor thread
        monitor_thread = threading.Thread(target=ranking_monitor, daemon=True)
        monitor_thread.start()
        
        # Start streaming scrape - this will call on_product_scraped for each product
        scrape_google_products_streaming(
            search_data.google_search_query,
            max_products=20,
            on_product_ready=on_product_scraped
        )
        
        # Signal that scraping is done
        scraping_done.set()
        print(f"[Task {task_id}] Scraping complete. Waiting for remaining rankings...")
        
        # Wait for monitor thread to finish processing all rankings
        monitor_thread.join(timeout=120)  # 2 min max wait
        
        # Shutdown executor
        rank_executor.shutdown(wait=False)
        
        # Sort by final score
        scored_products.sort(key=lambda x: x.get("scores", {}).get("final_score", 0), reverse=True)
        
        # Save ranked results to file
        safe_query = "".join([c if c.isalnum() else "_" for c in query])
        filename = f"ranked_{safe_query}.json"
        import json
        with open(filename, "w", encoding="utf-8") as f:
            json.dump([p for p in scored_products], f, indent=2, ensure_ascii=False)
        print(f"[Task {task_id}] ✓ Ranked results saved to {filename}")

        task_manager.update_task_progress(
            task_id,
            current_step="completed",
            step_message="🎉 Search complete! Here are your results.",
            progress_percent=100
        )

       
        # Mark task as completed with results
        task_manager.complete_task(task_id, scored_products)
        print(f"[Task {task_id}] ✓ Task completed successfully!")
        
    except Exception as e:
        print(f"[Task {task_id}] ✗ Error: {str(e)}")
        task_manager.update_task_progress(
            task_id,
            current_step="failed",
            step_message=f"❌ An error occurred: {str(e)[:100]}"
        )
        task_manager.fail_task(task_id, str(e))


@app.post(
    "/search",
    response_model=TaskCreatedResponse,
    tags=["Search"],
    summary="Start a product search",
    response_description="The created task with its ID and initial status",
)
async def start_search(request: SearchRequest, background_tasks: BackgroundTasks):
    """
    Start a new product search task.

    This endpoint creates an asynchronous search task and returns immediately
    with a task ID that can be used to poll for results.

    - **query**: The search query string to look for products
    - **country**: Country code for localized search results (default: US)

    Returns a task ID that can be used to check the status of the search.
    """
    task = task_manager.create_task(request.query)

    # Add the search task to background tasks
    background_tasks.add_task(run_search_task, task.id, request.query, request.country)

    return TaskCreatedResponse(task_id=task.id, status=task.status)


@app.get(
    "/search/{task_id}",
    response_model=TaskStatusResponse,
    tags=["Search"],
    summary="Get task status and results",
    response_description="The task status and results if completed",
    responses={
        404: {
            "description": "Task not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Task not found"}
                }
            }
        }
    }
)
async def get_task_status(task_id: str):
    """
    Get the status of a search task.

    Use this endpoint to poll for the status of a previously submitted search task.
    When the task is completed, the response will include the list of product URLs.

    - **task_id**: The UUID of the task to check
    """
    task = task_manager.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Sort partial results by score for display
    partial_results = sorted(
        task.scored_products,
        key=lambda x: x.get("scores", {}).get("final_score", 0),
        reverse=True
    ) if task.scored_products else []

    return TaskStatusResponse(
        task_id=task.id,
        status=task.status,
        query=task.query,
        result=task.result,
        error=task.error,
        current_step=task.current_step,
        step_message=task.step_message,
        total_products=task.total_products,
        scored_count=len(task.scored_products),
        progress_percent=task.progress_percent,
        partial_results=partial_results,
    )


@app.get(
    "/health",
    tags=["Health"],
    summary="Health check",
    response_description="API health status",
)
async def health_check():
    """
    Health check endpoint.

    Returns a simple status indicating the API is running.
    """
    return {"status": "healthy"}
