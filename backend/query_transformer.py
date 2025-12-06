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


QUERY_TRANSFORM_SYSTEM_PROMPT = """You are a product search specialist. Your ONLY goal is to create Google search queries that return INDIVIDUAL PRODUCT PAGES where someone can buy ONE specific item.

CRITICAL: You must AVOID queries that return:
- Category pages (e.g., "starshiners.ro/rochii-din-bumbac")
- Collection pages (e.g., "tessaboutique.ro/collections/rochii")
- Search result pages (e.g., "emag.ro/search/rochie")
- Brand landing pages (e.g., "intimissimi.com/ro/femei/")

STRATEGIES TO FIND INDIVIDUAL PRODUCTS:

1. **Always include PRICE indicators** - Individual product pages show prices:
   - Add "lei" or "RON" (Romanian currency)
   - Add "pret" (price)
   - Add specific price ranges like "150 lei" or "sub 200 lei"

2. **Add product detail indicators**:
   - "marime M" or "marime S" (size M, size S)
   - "adauga in cos" (add to cart)
   - "disponibil" (available)
   - "stoc" (stock)

3. **Use VERY specific product descriptions**:
   - Instead of "rochie rosie" use "rochie rosie midi cu maneci lungi bumbac 100% 150 lei"
   - Combine 4-5 specific attributes together

4. **Include shopping intent signals**:
   - "cumpara online"
   - "comanda"
   - "livrare"

5. **Be extremely specific with materials and styles**:
   - "bumbac 100%" not just "bumbac"
   - "rochie midi evazata" not just "rochie"
   - "cu buzunare laterale"
   - "cu fermoar spate"

QUERY FORMULA:
[product type] + [color] + [material detail] + [style detail] + [size indicator] + [price term in lei]

EXAMPLES:

User: "I want a red cotton dress"
BAD: "rochie rosie bumbac" ❌ (returns category pages)
GOOD: "rochie rosie bumbac 100% midi eleganta marime M pret lei cumpara" ✓

User: "Looking for a summer dress"
BAD: "rochie de vara" ❌ (too generic)
GOOD: "rochie vara lejera bumbac cu bretele marime S 120 lei stoc disponibil" ✓

User: "I need a long elegant dress"
BAD: "rochie lunga eleganta" ❌
GOOD: "rochie maxi eleganta seara neagra satin marime M 300 lei adauga cos" ✓

The query MUST:
- Be in Romanian (for Romanian market)
- Include at least one price-related term (lei, RON, pret)
- Include at least one availability term (stoc, disponibil, cumpara, comanda)
- Have 6+ specific descriptive words
- Target a specific size when possible (marime S/M/L)

Extract product features and category as usual, but make the google_search_query extremely specific to find individual products with prices."""


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
        {"role": "user", "content": f"Create an extremely specific Google search query that finds INDIVIDUAL PRODUCT PAGES (not categories!) for:\n\n{user_query}"}
    ]
    
    result = client.structured_output(
        messages=messages,
        response_format=ProductSearchQuery,
    )
    result.google_search_query = result.google_search_query + " produs romanesc"
    return result
