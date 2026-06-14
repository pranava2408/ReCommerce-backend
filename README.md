---
title: Second Life API
emoji: 🚀
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
---
# Second Life Commerce: AI Buyer Recommender Backend

## Overview
This is a high-performance FastAPI backend service designed to solve Amazon's "Fast Deviate" return logistics problem. 

When a perfectly usable item is cancelled by a buyer while in transit (or stranded at a nearby facility), returning it to the main warehouse wastes shipping costs and increases our carbon footprint. This AI engine intercepts that cancelled product and mathematically finds the **nearest neighbor human buyer** to deviate the shipment to directly.

## Features
- **Semantic Preferences Search:** Uses HuggingFace's lightweight `SentenceTransformers` (`all-MiniLM-L6-v2`) and FAISS (Facebook AI Similarity Search) to match the stranded product's specifications directly with Amazon buyers' search histories.
- **Geospatial Distance Filtering:** Calculates the exact physical distance between the stranded Amazon Facility and the potential Buyer using the Haversine formula (using precise Latitude and Longitude).
- **Fast Logistics Guarantee:** Automatically filters out buyers who live too far away from the facility and estimates delivery times (`Same Day`, `1-2 Days`) based on geographical proximity, ensuring rapid shipment deviation.

## Endpoints

### `POST /api/ingest-users`
Populates the FAISS vector database with your Amazon buyers.
- **Payload:** Array of Users (User ID, Latitude, Longitude, Search History text).
- **Action:** Generates 384-dimensional mathematical embeddings of what the users want and stores them in memory.

### `POST /api/recommend-buyers`
Finds the best buyers for a stranded product.
- **Payload:** Cancelled Product details (Product ID, Category, Specs, Facility Latitude & Longitude).
- **Action:** Vectorizes the product specs, queries FAISS for mathematically interested buyers, and applies a strict geographical radius filter.
- **Returns:** A sorted array of the best nearby buyers including their semantic match score and precise physical distance in kilometers.

## Tech Stack
- Python 3.10+
- FastAPI & Uvicorn
- Pydantic (Schema Validation)
- FAISS (Vector Database)
- HuggingFace SentenceTransformers
- Pytest (Unit Testing)

## Running Locally

1. **Activate the Virtual Environment**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

2. **Install Dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Start the Server**
   ```powershell
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

4. **Testing Interface**
   Open `http://127.0.0.1:8000/docs` in your browser to access the interactive Swagger UI and test the API manually.
