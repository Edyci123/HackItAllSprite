from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SearchRequest(BaseModel):
    query: str = Field(
        ...,
        description="The search query string to look for products",
        min_length=1,
        json_schema_extra={"example": "I want to buy my wife a dress. She likes red color and long dresses."}
    )
    country: str = Field(
        default="US",
        description="Country code for localized search results (e.g., US, RO, DE, FR)",
        min_length=2,
        max_length=2,
        json_schema_extra={"example": "RO"}
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"query": "I want a red long dress made of cotton", "country": "RO"},
                {"query": "wireless noise cancelling headphones", "country": "US"},
            ]
        }
    }


class TaskCreatedResponse(BaseModel):
    task_id: str = Field(
        ...,
        description="Unique identifier for the created task",
        json_schema_extra={"example": "550e8400-e29b-41d4-a716-446655440000"}
    )
    status: TaskStatus = Field(
        ...,
        description="Current status of the task",
        json_schema_extra={"example": "pending"}
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "task_id": "550e8400-e29b-41d4-a716-446655440000",
                    "status": "pending"
                }
            ]
        }
    }


class TaskStatusResponse(BaseModel):
    task_id: str = Field(
        ...,
        description="Unique identifier for the task",
        json_schema_extra={"example": "550e8400-e29b-41d4-a716-446655440000"}
    )
    status: TaskStatus = Field(
        ...,
        description="Current status of the task",
        json_schema_extra={"example": "completed"}
    )
    query: str = Field(
        ...,
        description="The original search query",
        json_schema_extra={"example": "wireless headphones"}
    )
    result: Optional[list[dict]] = Field(
        default=None,
        description="List of product dictionaries when the task is completed",
        json_schema_extra={"example": [
            {
                "name": "Product Name",
                "price": "100 lei",
                "link": "https://example.com/product/123",
                "image": "https://example.com/image.jpg",
                "firm": "Seller Name",
                "description": "Product Description"
            }
        ]}
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if the task failed",
        json_schema_extra={"example": None}
    )
    # Detailed progress fields
    current_step: str = Field(
        default="initializing",
        description="Current pipeline step: initializing, transforming, scraping, ranking, completed"
    )
    step_message: str = Field(
        default="Preparing your search...",
        description="Human-readable detailed status message"
    )
    total_products: int = Field(
        default=0,
        description="Total number of products found to rank"
    )
    scored_count: int = Field(
        default=0,
        description="Number of products that have been scored so far"
    )
    progress_percent: int = Field(
        default=0,
        description="Estimated progress percentage (0-100)"
    )
    partial_results: Optional[list[dict]] = Field(
        default=None,
        description="Products that have been scored so far (streaming results)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "task_id": "550e8400-e29b-41d4-a716-446655440000",
                    "status": "running",
                    "query": "wireless headphones",
                    "current_step": "ranking",
                    "step_message": "Analyzing product 5 of 20...",
                    "total_products": 20,
                    "scored_count": 5,
                    "progress_percent": 45,
                    "partial_results": [],
                    "result": None,
                    "error": None
                }
            ]
        }
    }
