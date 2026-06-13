from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_buyer_recommender():
    # 1. Ingest Mock Users
    users = [
        {
            "user_id": "u1",
            "latitude": 34.0522, # Los Angeles
            "longitude": -118.2437,
            "search_history": "Apple iPhone 13, AirPods, Macbooks"
        },
        {
            "user_id": "u2",
            "latitude": 40.7128, # New York
            "longitude": -74.0060,
            "search_history": "Apple iPhone 13, Phone cases"
        },
        {
            "user_id": "u3",
            "latitude": 34.0195, # Santa Monica (Close to LA)
            "longitude": -118.4912,
            "search_history": "Gaming laptops, mechanical keyboards"
        }
    ]
    resp = client.post("/api/ingest-users", json=users)
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"

    # 2. Stranded Product in Los Angeles Facility
    stranded_product = {
        "product_id": "p101",
        "category": "Electronics",
        "specs": "Apple iPhone 13, 128GB, Midnight",
        "facility_latitude": 34.0520, # LA facility
        "facility_longitude": -118.2430
    }
    
    # Query for recommendations
    resp2 = client.post("/api/recommend-buyers", params={"max_distance_km": 100.0, "k": 3}, json=stranded_product)
    assert resp2.status_code == 200
    results = resp2.json()
    
    # u1 (LA) wants iPhones and is very close to LA facility. Should be recommended.
    # u2 (NY) wants iPhones but is 3000 miles away. Should be filtered out by distance!
    # u3 (Santa Monica) is close to LA facility, but doesn't want iPhones. Should have a poor semantic score or be filtered out depending on the K.
    
    recommended_user_ids = [r["user_id"] for r in results]
    assert "u1" in recommended_user_ids
    assert "u2" not in recommended_user_ids # Blocked by max_distance_km
