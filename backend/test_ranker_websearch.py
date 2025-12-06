
from ranker import rank_products
import json

# Dummy product data
products = [
    {
        "name": "Iphone 15 Pro",
        "price": "5000 RON",
        "firm": "eMAG",
        "description": "Latest iphone",
        "link": "https://emag.ro/iphone"
    },
    {
        "name": "Iphone 15 Pro",
        "price": "4900 RON",
        "firm": "UnknownSmallShop",
        "description": "Latest iphone sealed",
        "link": "https://unknownshop.ro/iphone"
    }
]

user_query = "iphone 15 pro de la un magazin romanesc mic"

ranked = rank_products(products, user_query)
print(json.dumps(ranked, indent=2))
