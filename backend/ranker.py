import concurrent.futures
from pydantic import BaseModel, Field
from llm_client import get_llm_client

class ProductScore(BaseModel):
    small_business_score: int = Field(description="0-100. High for small/unknown businesses, Low (0-20) for giants like eMag, Amazon.")
    trust_score: int = Field(description="0-100. Based on reviews/reputation. 50 if unknown.")
    similarity_score: int = Field(description="0-100. How well the product matches the user's specific request.")
    final_score: int = Field(description="Weighted average: 40% Small Biz, 30% Similarity, 30% Trust.")
    reasoning: str = Field(description="Brief explanation of the scores. Mention any sources found via web search.")

def score_product(product: dict, user_query: str) -> dict:
    """
    Scores a single product using the LLM with web search capabilities.
    """
    client = get_llm_client()
    
    prompt = f"""You are a product ranking expert.
Your goal is to score this product based on 3 criteria.
You have access to a **web_search** tool. You MUST use it to find information about the seller/firm if you don't know them.

1. **Small Business Score** (High numeric value = GOOD):
   - We want to support smaller, local businesses.
   - If the seller is a giant (eMag, Amazon, Altex, Zara, H&M, AboutYou, Epantofi, etc.), give a VERY LOW score (0-20).
   - If it's a small/medium Romanian business (turnover < 10M EUR or unknown brand), give a HIGH score (80-100).
   - **USE WEB SEARCH** to check the firm's size ("cifra de afaceri listafirme").

2. **Trust Score** (High numeric value = GOOD):
   - **USE WEB SEARCH** to check reviews (Reddit, Trustpilot, "pareri", "teapa").
   - If scams/teapa mentioned -> 0.
   - If mixed reviews -> 40-60.
   - If good reputation -> 80-100.
   - If no info found after searching -> 50 (Neutral).

3. **Similarity Score** (High numeric value = GOOD):
   - How well does the product '{product.get('name')}' match the User Query: "{user_query}"?
   - Check materials, color, style, price.

4. **Final Calculation**:
   - Small Business: 40%
   - Similarity: 30%
   - Trust: 30%

Product Details:
Name: {product.get('name')}
Price: {product.get('price')}
Seller: {product.get('firm')}
Description: {product.get('description')}
Link: {product.get('link')}

Output ONLY a valid JSON object with the following structure:
{{
    "small_business_score": int,
    "trust_score": int,
    "similarity_score": int,
    "final_score": int,
    "reasoning": "string with citations"
}}
"""

    try:
        response_text = client.create_response(
            input_text=prompt,
            tools=[{"type": "web_search"}],
            # If gpt-4o-mini is not supported for responses, we might default to whatever works or let the user config override.
            # However, the user documentation examples use "gpt-5" or "o4-mini".
            # Safe bet: try to use the default model from client, if it fails, we might need to change the default model in llm_client.
        )
        
        # Strip markdown syntax if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
            
        import json
        score_data = json.loads(response_text)
        
        return {
            **product,
            "scores": score_data
        }
    except Exception as e:
        print(f"Error scoring product {product.get('name')}: {e}")
        # Return with default scores
        return {
            **product,
            "scores": {
                "small_business_score": 50,
                "trust_score": 50,
                "similarity_score": 0,
                "final_score": 0,
                "reasoning": "Error during scoring"
            }
        }

def rank_products(products: list[dict], user_query: str) -> list[dict]:
    """
    Ranks a list of products using LLM-based scoring with integrated web search.
    """
    if not products:
        return []

    print(f"Ranking {len(products)} products using Agentic Web Search...")
    
    scored_products = []
    
    # We can probably increase max_workers slightly as we are not doing manual scraping anymore, 
    # but we are hitting OpenAI API which has rate limits.
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for product in products:
            futures.append(executor.submit(score_product, product, user_query))
            
        for future in concurrent.futures.as_completed(futures):
            scored_products.append(future.result())

    # Sort by Final Score Descending
    scored_products.sort(key=lambda x: x["scores"]["final_score"], reverse=True)
    
    return scored_products
