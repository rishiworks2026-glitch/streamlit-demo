from typing import Dict

def recommend_promotion(product: Dict) -> Dict:
    days = product.get('days_since_sale', 999)
    qty = product.get('quantity', 0)
    suggestion = {"type": "none", "message": "Healthy stock"}
    if days >= 90:
        suggestion = {"type": "clearance", "message": "Clearance sale recommended (deep discount)"}
    elif days >= 60:
        suggestion = {"type": "discount", "message": "Recommend 15-25% discount"}
    elif days >= 30:
        suggestion = {"type": "bogo", "message": "Buy 1 Get 1 or bundle with a popular item"}

    # Quantity-based tweak
    if qty >= 100 and days >= 30:
        suggestion['message'] += "; consider bundling or bulk discount for large stock"

    return suggestion
