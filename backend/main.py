from fastapi import FastAPI, HTTPException, BackgroundTasks

from models import SearchRequest, TaskCreatedResponse, TaskStatusResponse, TaskStatus
from tasks import task_manager
from query_transformer import transform_user_query

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
3. **Get results** - When completed, the response includes product URLs

### Task Statuses:
- `pending` - Task created, waiting to start
- `running` - Search in progress
- `completed` - Search finished, results available
- `failed` - Search failed, error message available
    """,
    version="1.0.0",
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
)


def run_search_task(task_id: str, query: str, country: str = "US"):
    """
    Background task that performs the actual product search pipeline.
    
    Pipeline:
    1. Transform user query → Google search query + features
    2. SERP scrape → Get URLs from Google
    3. TODO: Filter/analyze results based on features
    """
    try:
        # Update task status to running
        task_manager.update_task_status(task_id, TaskStatus.RUNNING)

        # Step 1: Transform user query into structured search data
        print(f"[Task {task_id}] Step 1: Transforming user query...")
        search_data = transform_user_query(query)
        print(f"[Task {task_id}] ✓ Google Query: {search_data.google_search_query}")
        print(f"[Task {task_id}] ✓ Features: {search_data.product_features}")
        print(f"[Task {task_id}] ✓ Category: {search_data.product_category}")

       
        # Mark task as completed with results
        task_manager.complete_task(task_id, [])
        print(f"[Task {task_id}] ✓ Task completed successfully!")
        
    except Exception as e:
        print(f"[Task {task_id}] ✗ Error: {str(e)}")
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

    return TaskStatusResponse(
        task_id=task.id,
        status=task.status,
        query=task.query,
        result=task.result,
        error=task.error,
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
