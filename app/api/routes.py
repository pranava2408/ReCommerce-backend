from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.models.schemas import UserIn, CancelledProduct, RecommendedBuyer
from app.services.buyer_recommender import BuyerRecommender

router = APIRouter()

def get_recommender() -> BuyerRecommender:
    return BuyerRecommender()

# We no longer use a mock database. Data is fetched directly from Supabase.
STRANDED_PRODUCTS = []

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
        from app.config import SUPABASE_URL, SUPABASE_KEY
        from supabase import create_client, Client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        deals_for_user = []
        
        # Query Supabase for stranded products (Items with status RECEIVED)
        items_resp = supabase.table("Item").select("id, name, originalPrice, status, Category(name), Location(latitude, longitude)").eq("status", "RECEIVED").execute()
        stranded_items = items_resp.data
        
        # If DB is empty, use our mock data fallback just for the demo
        if not stranded_items:
            stranded_items = [
                {
                    "id": "sp-101",
                    "Category": {"name": "Electronics"},
                    "name": "Apple iPhone 13, 128GB, Midnight - Perfect Condition",
                    "Location": {"latitude": 34.0520, "longitude": -118.2430},
                    "originalPrice": 79900.00
                },
                {
                    "id": "sp-102",
                    "Category": {"name": "Computers"},
                    "name": "Razer Blade 15 Gaming Laptop, RTX 3070",
                    "Location": {"latitude": 40.7120, "longitude": -74.0050},
                    "originalPrice": 249900.00
                }
            ]
        
        for sp in stranded_items:
            cat_name = sp.get("Category", {}).get("name", "General") if sp.get("Category") else "General"
            loc = sp.get("Location") or {}
            lat = loc.get("latitude") or 34.0520
            lon = loc.get("longitude") or -118.2430
            orig_price = sp.get("originalPrice", 0)
            
            # We run the recommender engine to see who wants this product
            product_dict = CancelledProduct(
                product_id=str(sp["id"]),
                category=cat_name,
                specs=sp.get("name", "Unknown item"),
                facility_latitude=lat,
                facility_longitude=lon
            ).model_dump()
            
            # Find the best buyers for this product
            recommended = engine.recommend_buyers(product_dict, max_distance_km=200.0, k=5)
            
            # If the current user_id is in the recommended list, this is a deal for them!
            user_match = next((r for r in recommended if r["user_id"] == user_id), None)
            
            if user_match:
                deviate_price = float(orig_price) * 0.85 # 15% off logic
                deals_for_user.append({
                    "product_id": str(sp["id"]),
                    "category": cat_name,
                    "specs": sp.get("name", "Unknown item"),
                    "original_price": float(orig_price),
                    "deviate_price": deviate_price,
                    "distance_km": user_match["distance_km"],
                    "estimated_delivery_days": user_match["estimated_delivery_days"],
                    "semantic_match_score": user_match["semantic_match_score"]
                })
                
        return {"status": "success", "deals": deals_for_user}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

