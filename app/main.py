from fastapi import FastAPI
from app.api.routes import router as api_router
from app.services.buyer_recommender import BuyerRecommender
from contextlib import asynccontextmanager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up API, initializing BuyerRecommender...")
    BuyerRecommender()
    yield
    logger.info("Shutting down API...")

app = FastAPI(
    title="Amazon Fast Deviate Recommender API",
    description="High-performance AI backend for matching cancelled products to nearby buyers.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(api_router, prefix="/api")

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}
