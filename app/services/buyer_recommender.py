import logging
import threading
import math
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance in kilometers between two points 
    on the earth (specified in decimal degrees). This is the standard practice
    used by logistics providers for "as the crow flies" physical distance.
    """
    # Convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])

    # Haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    r = 6371 # Radius of earth in kilometers
    return c * r

class BuyerRecommender:
    """
    A Singleton class for managing the HuggingFace SentenceTransformer model
    and the FAISS vector index, but mapped for User -> Product affinity.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, model_name: str = 'all-MiniLM-L6-v2'):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(BuyerRecommender, cls).__new__(cls)
                cls._instance._initialize(model_name)
        return cls._instance

    def _initialize(self, model_name: str):
        logger.info(f"Loading SentenceTransformer model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        logger.info(f"Model loaded. Embedding dimension: {self.dimension}")
        
        self.index = faiss.IndexFlatL2(self.dimension)
        self.id_to_user = {}
        self.current_id = 0

    def add_users(self, users: list[dict]) -> None:
        """
        Ingest Amazon user profiles and their search history into the vector index.
        """
        if not users:
            return
            
        texts = [u.get('search_history', '') for u in users]
        
        # FAISS requires float32
        embeddings = self.model.encode(texts, convert_to_numpy=True).astype(np.float32)
        assert embeddings.shape[1] == self.dimension, f"Embedding dimension mismatch!"
        
        start_id = self.current_id
        self.index.add(embeddings)
        
        for i, user in enumerate(users):
            self.id_to_user[start_id + i] = user
            
        self.current_id += len(users)
        logger.info(f"Added {len(users)} users to the vector store. Total users indexed: {self.current_id}")

    def recommend_buyers(self, product: dict, max_distance_km: float = 200.0, k: int = 5) -> list[dict]:
        """
        Takes a stranded product and finds the mathematically nearest Users who:
        1. Have search history strongly matching the product
        2. Are geographically close to the facility to guarantee fast 1-2 day shipping
        """
        if self.current_id == 0:
            return []
            
        category = product.get('category', '')
        specs = product.get('specs', '')
        text = f"Looking for {category} with specs: {specs}"
        
        query_vector = self.model.encode([text], convert_to_numpy=True).astype(np.float32)
        
        # Pull 10x the requested limit from the vector database because we are going 
        # to filter them geographically. We need a larger pool first.
        search_k = min(k * 10, self.current_id) 
        
        distances, indices = self.index.search(query_vector, search_k)
        
        facility_lat = product.get('facility_latitude', 0.0)
        facility_lon = product.get('facility_longitude', 0.0)
        
        results = []
        for i in range(search_k):
            faiss_id = indices[0][i]
            if faiss_id != -1 and faiss_id in self.id_to_user:
                user = self.id_to_user[faiss_id]
                
                # Standard practice physical distance
                dist_km = haversine_distance(
                    facility_lat, facility_lon,
                    user['latitude'], user['longitude']
                )
                
                # Strict logistical filter for Amazon 1-2 day deviated shipping
                if dist_km <= max_distance_km:
                    estimated_days = "Same Day" if dist_km < 30 else ("1-2 Days" if dist_km < 200 else "3+ Days")
                    results.append({
                        "user_id": user["user_id"],
                        "semantic_match_score": float(distances[0][i]),
                        "distance_km": round(dist_km, 2),
                        "estimated_delivery_days": estimated_days
                    })
                    
        # Since FAISS returned the most mathematically interested people first, 
        # this final list represents the most interested people who ALSO live close.
        return results[:k]
