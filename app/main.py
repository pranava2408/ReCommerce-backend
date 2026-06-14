from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
from app.services.buyer_recommender import BuyerRecommender
from contextlib import asynccontextmanager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up API, initializing BuyerRecommender...")
    engine = BuyerRecommender()
    
    try:
        from app.config import SUPABASE_URL, SUPABASE_KEY
        from supabase import create_client, Client
        
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Fetch real users from Supabase
        users_resp = supabase.table("User").select("id, email, Order(Item(name, Category(name)))").execute()
        users_data = users_resp.data
        
        formatted_users = []
        for u in users_data:
            # Build search history from orders
            history_items = []
            for o in u.get("Order", []):
                item = o.get("Item", {})
                if item:
                    cat = item.get("Category", {}).get("name", "") if item.get("Category") else ""
                    name = item.get("name", "")
                    history_items.append(f"{cat} {name}".strip())
            
            search_history = ", ".join(history_items) if history_items else f"Electronics, Gadgets for {u.get('email', '')}"
            
            formatted_users.append({
                "user_id": str(u["id"]),
                "latitude": 34.0522, # Defaulting due to lack of User location in schema
                "longitude": -118.2437,
                "search_history": search_history
            })
            
        if not formatted_users:
            logger.warning("No users found in Supabase! Adding fallback mock user.")
            formatted_users.append({
                "user_id": "buyer-la-001",
                "latitude": 34.0522,
                "longitude": -118.2437,
                "search_history": "Apple iPhone 13, AirPods, Macbooks"
            })
            
        engine.add_users(formatted_users)
        logger.info(f"Successfully seeded {len(formatted_users)} users from Supabase.")
    except Exception as e:
        logger.error(f"Failed to fetch users from Supabase: {e}")
        
    yield
    logger.info("Shutting down API...")

app = FastAPI(
    title="Amazon Fast Deviate Recommender API",
    description="High-performance AI backend for matching cancelled products to nearby buyers.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}
