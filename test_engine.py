from app.services.vector_store import VectorStore

def main():
    print("Initializing VectorStore (this will download the lightweight model the first time)...")
    store = VectorStore()
    
    # Mock inventory of second-life products
    inventory = [
        {"id": "p1", "category": "Electronics", "condition": "Refurbished", "specs": "Smartphone, 128GB, Black"},
        {"id": "p2", "category": "Electronics", "condition": "Used - Good", "specs": "Smartphone, 64GB, Black"},
        {"id": "p3", "category": "Furniture", "condition": "Like New", "specs": "Wooden Chair, Oak"},
        {"id": "p4", "category": "Electronics", "condition": "Refurbished", "specs": "Laptop, 16GB RAM, 512GB SSD"},
    ]
    
    print("\nIngesting inventory into FAISS...")
    store.add_products(inventory)
    
    # A cancelled order we want to find alternatives for
    cancelled_order = {"category": "Electronics", "condition": "New", "specs": "Smartphone, 128GB, White"}
    
    print("\nFinding nearest alternatives for cancelled order:")
    print(f"Cancelled Item: {cancelled_order}")
    
    results = store.find_nearest_neighbors(cancelled_order, k=2)
    
    print("\n--- Top 2 Alternatives Found ---")
    for res in results:
        # Lower L2 distance means it's a closer match
        print(f"ID: {res['id']} | Specs: {res['specs']} | Condition: {res['condition']} | (L2 Distance: {res['l2_distance']:.4f})")

if __name__ == "__main__":
    main()
