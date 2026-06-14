from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.models.schemas import UserIn, CancelledProduct, RecommendedBuyer
from app.services.buyer_recommender import BuyerRecommender

router = APIRouter()

def get_recommender() -> BuyerRecommender:
    return BuyerRecommender()

# Mock database of currently stranded products in the logistics network
STRANDED_PRODUCTS = [
    {
        "product_id": "sp-101",
        "category": "Electronics",
        "specs": "Apple iPhone 13, 128GB, Midnight - Perfect Condition",
        "facility_latitude": 34.0520, # Los Angeles
        "facility_longitude": -118.2430,
        "original_price": 79900.00,
        "deviate_price": 69900.00
    },
    {
        "product_id": "sp-102",
        "category": "Computers",
        "specs": "Razer Blade 15 Gaming Laptop, RTX 3070",
        "facility_latitude": 40.7120, # New York
        "facility_longitude": -74.0050,
        "original_price": 249900.00,
        "deviate_price": 199900.00
    },
    {
        "product_id": "sp-103",
        "category": "Electronics",
        "specs": "Apple AirPods Pro (2nd Generation)",
        "facility_latitude": 34.0200, # Los Angeles
        "facility_longitude": -118.4900,
        "original_price": 24900.00,
        "deviate_price": 19900.00
    },
    {
        "product_id": "sp-104",
        "category": "Computers",
        "specs": "Apple MacBook Air M2, 8GB RAM, 256GB SSD",
        "facility_latitude": 34.1000, # Los Angeles
        "facility_longitude": -118.3000,
        "original_price": 109900.00,
        "deviate_price": 89900.00
    }
]

@router.post("/ingest-users", summary="Populate the engine with Amazon buyers and their preferences")
def ingest_users(users: List[UserIn], engine: BuyerRecommender = Depends(get_recommender)):
    try:
        user_dicts = [u.model_dump() for u in users]
        engine.add_users(user_dicts)
        return {"status": "success", "message": f"Successfully ingested {len(users)} buyers into the recommendation engine."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recommend-buyers", response_model=List[RecommendedBuyer], summary="Find the best nearby buyers to deviate a cancelled product to")
def recommend_buyers(
    cancelled_product: CancelledProduct, 
    max_distance_km: float = 200.0, 
    k: int = 5, 
    engine: BuyerRecommender = Depends(get_recommender)
):
    try:
        product_dict = cancelled_product.model_dump()
        results = engine.recommend_buyers(product_dict, max_distance_km=max_distance_km, k=k)
        
        response = [RecommendedBuyer(**res) for res in results]
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/buyer-deals/{user_id}", summary="Get personalized Fast Deviate deals for a specific buyer")
def get_buyer_deals(user_id: str, engine: BuyerRecommender = Depends(get_recommender)):
    """
    Inverse endpoint for the frontend. Given a buyer logging in, find if any 
    currently stranded products are a match for them.
    """
    try:
        deals_for_user = []
        
        # In a real app, we'd query the DB for all active stranded products. 
        # Here we loop over our mock database.
        for sp in STRANDED_PRODUCTS:
            # We run the recommender engine to see who wants this product
            product_dict = CancelledProduct(
                product_id=sp["product_id"],
                category=sp["category"],
                specs=sp["specs"],
                facility_latitude=sp["facility_latitude"],
                facility_longitude=sp["facility_longitude"]
            ).model_dump()
            
            # Find the best buyers for this product
            recommended = engine.recommend_buyers(product_dict, max_distance_km=200.0, k=5)
            
            # If the current user_id is in the recommended list, this is a deal for them!
            user_match = next((r for r in recommended if r["user_id"] == user_id), None)
            
            if user_match:
                deals_for_user.append({
                    "product_id": sp["product_id"],
                    "category": sp["category"],
                    "specs": sp["specs"],
                    "original_price": sp["original_price"],
                    "deviate_price": sp["deviate_price"],
                    "distance_km": user_match["distance_km"],
                    "estimated_delivery_days": user_match["estimated_delivery_days"],
                    "semantic_match_score": user_match["semantic_match_score"]
                })
                
        return {"status": "success", "deals": deals_for_user}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
