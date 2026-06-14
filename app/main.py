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
    
    # Pre-seed the engine with mock users so the frontend has data to query
    mock_users = [
        {
            "user_id": "buyer-la-001",
            "latitude": 34.0522,
            "longitude": -118.2437,
            "search_history": "Apple iPhone 13, AirPods, Macbooks"
        },
        {
            "user_id": "buyer-ny-002",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "search_history": "Razer Blade Gaming Laptop"
        }
    ]
    engine.add_users(mock_users)
    
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
