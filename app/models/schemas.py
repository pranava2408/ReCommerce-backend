from pydantic import BaseModel, Field
from typing import Optional

class UserIn(BaseModel):
    user_id: str = Field(..., description="Unique identifier for the user")
    latitude: float = Field(..., description="User's geographic latitude")
    longitude: float = Field(..., description="User's geographic longitude")
    search_history: str = Field(..., description="Textual summary of what the user browses or buys")

class CancelledProduct(BaseModel):
    product_id: str = Field(..., description="Unique identifier for the stranded product")
    category: str = Field(..., description="Category of the product")
    specs: str = Field(..., description="Key specifications of the product")
    facility_latitude: float = Field(..., description="Latitude of the facility where the product is stranded")
    facility_longitude: float = Field(..., description="Longitude of the facility where the product is stranded")

class RecommendedBuyer(BaseModel):
    user_id: str = Field(..., description="Unique identifier for the recommended user")
    semantic_match_score: float = Field(..., description="How closely their search history matches the product (L2 distance)")
    distance_km: float = Field(..., description="Distance between user and facility in kilometers")
    estimated_delivery_days: str = Field(..., description="Estimated delivery time based on proximity")
