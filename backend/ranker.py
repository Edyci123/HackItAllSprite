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
    Scores a single product using the LLM with structured output.
    Uses OpenAI's Structured Outputs API for guaranteed valid responses.
    """
    client = get_llm_client()
    
    prompt = f"""Ești un expert în shopping și analiză de afaceri locale din România.
Scopul tău este să analizezi acest produs pentru un utilizator din România care vrea să susțină afacerile locale mici.

1. **Scor Afacere Mică** (Small Business Score):
   - Căutăm producători locali, afaceri românești mici.
   - Dacă vânzătorul este un gigant (eMag, Amazon, Altex, Zara, H&M, AboutYou, Epantofi, Dedeman etc.), dă un scor FOARTE MIC (0-15).
   - Dacă este o afacere mică/medie românească sau un brand local, dă un scor MARE (85-100).

2. **Scor Încredere** (Trust Score):
   - Reputație bună -> 80-100.
   - Lipsă informații -> 50.

3. **Scor Similitudine** (Similarity Score):
   - Cât de bine se potrivește produsul '{product.get('name')}' cu ce a cerut utilizatorul: "{user_query}"?

4. **Raționament (Reasoning - FOARTE IMPORTANT)**:
   - Scrie ÎNTOTDEAUNA în limba ROMÂNĂ.
   - Concentrează-te EXCLUSIV pe COMPANIE/VÂNZĂTOR, nu pe produs.
   - Menționează informații despre afacerea "{product.get('firm')}":
     * Este o afacere locală românească sau un lanț mare?
     * Ce fel de companie este? (atelier, magazin de familie, producător local, brand românesc)
     * De cât timp există pe piață (dacă știi)?
     * Ce o face specială sau diferită?
   - Scrie 2-3 fraze SCURTE și ATRĂGĂTOARE care să invite la cumpărare.
   - Exemplu pentru afacere mică: "Furnizat de [Firm], un atelier local care creează produse artizanale din 2015. Susține economia locală alegând această afacere românească!"
   - Exemplu pentru firmă mare: "Disponibil de la [Firm], un retailer de încredere cu livrare rapidă."
   - NU menționa scoruri sau numere.

5. **Final Score**: Calculate as weighted average: 40% Small Biz, 30% Similarity, 30% Trust.

Detalii Produs:
Nume: {product.get('name')}
Preț: {product.get('price')}
Vânzător/Companie: {product.get('firm')}
Descriere: {product.get('description')}
Link: {product.get('link')}
"""

    try:
        # Use structured output API for guaranteed valid response format
        score_result = client.structured_output(
            messages=[
                {"role": "system", "content": "You are a product scoring expert. Always respond with the exact JSON structure requested."},
                {"role": "user", "content": prompt}
            ],
            response_format=ProductScore,
            temperature=0.3,
        )
        
        return {
            **product,
            "scores": score_result.model_dump()
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

def rank_products(products: list[dict], user_query: str, on_product_scored=None) -> list[dict]:
    """
    Ranks a list of products using LLM-based scoring with integrated web search.
    
    Args:
        products: List of product dictionaries to score
        user_query: Original user search query
        on_product_scored: Optional callback(scored_product, index, total) called after each product is scored
    """
    if not products:
        return []

    print(f"Ranking {len(products)} products using Agentic Web Search...")
    
    scored_products = []
    total = len(products)
    
    # We can probably increase max_workers slightly as we are not doing manual scraping anymore, 
    # but we are hitting OpenAI API which has rate limits.
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for product in products:
            futures.append(executor.submit(score_product, product, user_query))
            
        for future in concurrent.futures.as_completed(futures):
            scored_product = future.result()
            scored_products.append(scored_product)
            
            # Call the callback if provided (for streaming)
            if on_product_scored:
                on_product_scored(scored_product, len(scored_products), total)

    # Sort by Final Score Descending
    scored_products.sort(key=lambda x: x["scores"]["final_score"], reverse=True)
    
    return scored_products
