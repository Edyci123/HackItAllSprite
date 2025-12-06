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

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "task_id": "550e8400-e29b-41d4-a716-446655440000",
                    "status": "completed",
                    "query": "wireless headphones",
                    "result": [
                        "https://example.com/product/123",
                        "https://example.com/product/456"
                    ],
                    "error": None
                }
            ]
        }
    }
