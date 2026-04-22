import json
import chromadb

print("Connecting to ChromaDB on port 8000...")
client = chromadb.HttpClient(host="localhost", port=8000)

collection = client.get_or_create_collection(name="travel_rag_collection")

with open("plans/rovaniemi_locations.json", "r", encoding="utf-8") as file:
    locations = json.load(file)

ids = []
documents = []
metadatas = []

print("Processing data...")
for loc in locations:
    ids.append(loc["id"])
    
    documents.append(loc["description"])
    
    metadatas.append({
        "name": loc["name"],
        "category": loc["category"],
        "importance_score": loc["importance_score"],
        "cost_tier": loc["cost_tier"],
        "lat": loc["location"]["lat"],
        "lon": loc["location"]["lon"],
        "vibe_tags": ", ".join(loc["vibe_tags"]), 
        "city": loc["city"],
        "opening_time": loc.get("opening_time", "00:00"),
        "closing_time": loc.get("closing_time", "23:59")
    })

print(f"Adding {len(documents)} locations into the vector database")
collection.upsert(
    ids=ids,
    documents=documents,
    metadatas=metadatas
)