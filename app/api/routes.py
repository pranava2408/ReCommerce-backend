from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.models.schemas import UserIn, CancelledProduct, RecommendedBuyer
from app.services.buyer_recommender import BuyerRecommender

router = APIRouter()

def get_recommender() -> BuyerRecommender:
    return BuyerRecommender()

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
