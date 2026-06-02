import json
import requests
import chromadb

def build_city_matrix(city_name):
    print(f"Building distance matrix for {city_name}...")
    
    client = chromadb.HttpClient(host="localhost", port=8000)
    collection = client.get_collection(name="travel_rag_collection")
    
    results = collection.query(
        query_texts=[city_name], 
        n_results=100, 
        where={"city": city_name}
    )
    
    locations = []
    for i in range(len(results['ids'][0])):
        locations.append({
            "id": results['ids'][0][i], 
            "lat": results['metadatas'][0][i]['lat'],
            "lon": results['metadatas'][0][i]['lon']
        })
        
    if not locations:
        print(f"No locations found for {city_name}!")
        return

    coords_string = ";".join([f"{loc['lon']},{loc['lat']}" for loc in locations])
    
    url = f"http://router.project-osrm.org/table/v1/foot/{coords_string}"
    print("Asking OSRM to calculate all possible routes... this might take a few seconds.")
    response = requests.get(url)
    data = response.json()
    
    if data.get("code") != "Ok":
        print("Error from OSRM:", data)
        return

    durations = data["durations"]
    distance_matrix = {}
    
    for i, origin in enumerate(locations):
        distance_matrix[origin["id"]] = {}
        for j, destination in enumerate(locations):
            distance_matrix[origin["id"]][destination["id"]] = durations[i][j]
            
    filename = f"{city_name.lower()}_matrix.json"
    with open(filename, 'w') as f:
        json.dump(distance_matrix, f, indent=4)
        
    print(f"Success! Saved {len(locations)}x{len(locations)} routing grid to {filename}")

build_city_matrix("Dublin")
