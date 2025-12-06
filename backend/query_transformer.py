from pydantic import BaseModel, Field
from llm_client import get_llm_client


class ProductSearchQuery(BaseModel):
    """Structured output for transforming user product descriptions into search-ready formats."""
    
    google_search_query: str = Field(
        description="A highly specific Google search query that finds INDIVIDUAL PRODUCT PAGES with prices, "
                    "NOT category pages, collection pages, or search results. Must include price-related terms."
    )
    
    product_features: list[str] = Field(
        description="A list of specific product features/requirements extracted from the user's description. "
                    "Each feature should be a short, clear phrase that can be used for filtering products."
    )
    
    product_category: str = Field(
        description="The general product category (e.g., 'dress', 'laptop', 'headphones')"
    )


QUERY_TRANSFORM_SYSTEM_PROMPT = """You are a Google Search query optimizer. Your goal is to convert a user's natural language request into a clean, effective search query in Romanian.

Instructions:
1. Extract the core product keywords: Product Type, Material, Color, Style.
2. Translate to Romanian if the input is in English.
3. Remove conversational filler words (e.g., "I want to buy", "looking for", "she likes").
4. Keep it concise. Do not add highly specific filters (like "pret", "stoc") unless the user explicitly asked for them.

EXAMPLES:

User: "I want to buy my wife a nice long dress. She likes the color red and she enjoys a natural material."
Query: "rochie lunga rosie bumbac"

User: "Looking for wireless headphones with noise cancelling"
Query: "casti wireless noise cancelling"

User: "cheap running shoes for men"
Query: "adidasi alergare barbati ieftini"
"""


def transform_user_query(user_query: str) -> ProductSearchQuery:
    """
    Transform a complex user product description into a structured search query.
    
    Args:
        user_query: The user's natural language product description
        
    Returns:
        ProductSearchQuery with google_search_query, product_features, and product_category
    """
    client = get_llm_client()
    
    messages = [
        {"role": "system", "content": QUERY_TRANSFORM_SYSTEM_PROMPT},
        {"role": "user", "content": user_query}
    ]
    
    result = client.structured_output(
        messages=messages,
        response_format=ProductSearchQuery,
    )
    result.google_search_query = result.google_search_query + " produs romanesc"
    return result
