import os
import math
import json
import numpy as np
import chromadb
from sklearn.cluster import KMeans
from groq import Groq
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from functools import lru_cache

load_dotenv()

app = FastAPI(title="Travel AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


@lru_cache(maxsize=1)
def get_chroma_collection():
    client = chromadb.HttpClient(host="localhost", port=8000)
    return client.get_collection(name="travel_rag_collection")


@lru_cache(maxsize=1)
def load_matrices():
    matrices = {}
    cities = ["Prague", "Rovaniemi", "Budapest"]
    for city in cities:
        try:
            with open(f"maps/{city.lower()}_matrix.json", "r") as f:
                matrices[city] = json.load(f)
        except FileNotFoundError:
            pass
    return matrices


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    city: Optional[str] = None
    budget: Optional[str] = None
    start_point_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    city: Optional[str]
    budget: Optional[str]
    start_point_id: Optional[str]
    start_point_name: Optional[str]
    info: Optional[str]


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        collection = get_chroma_collection()
    except Exception:
        raise HTTPException(status_code=503, detail="Could not connect to ChromaDB. Is Docker running?")

    city_matrices = load_matrices()

    current_city = req.city
    budget_val = req.budget or "Unknown"
    start_point_id = req.start_point_id

    prompt = req.messages[-1].content if req.messages else ""

    intake_prompt = f"""
You are a strict data-extraction agent. Analyze the user's travel request and extract parameters.
Return ONLY a valid JSON object. Do not include markdown formatting like ```json.

Required Keys:
- "city": The name of the city (e.g., "Prague"), or "Unknown" if not mentioned.
- "budget": MUST be one of ["OnlyFreePlaces", "LimitedBudget", "MostPlacesAllowed", "OnlyHighEndPlaces", "Unknown"].
- "start_point": The specific location they want to start at, or "None".

User Request: '{prompt}'
"""

    extraction_response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "system", "content": intake_prompt}],
        temperature=0,
        response_format={"type": "json_object"},
    ).choices[0].message.content.strip()

    extracted_data = json.loads(extraction_response)

    if extracted_data.get("city") != "Unknown":
        current_city = extracted_data["city"]

    if not current_city:
        return ChatResponse(
            reply="I couldn't tell which city you want to visit! Could you please specify?",
            city=None,
            budget=budget_val,
            start_point_id=start_point_id,
            start_point_name=None,
            info=None,
        )

    extracted_budget = extracted_data.get("budget", "Unknown")
    if extracted_budget != "Unknown":
        budget_val = extracted_budget

    if budget_val == "OnlyFreePlaces":
        cost_filter = ["Free"]
    elif budget_val == "LimitedBudget":
        cost_filter = ["$", "Free"]
    elif budget_val == "MostPlacesAllowed":
        cost_filter = ["Free", "$", "$$"]
    elif budget_val == "OnlyHighEndPlaces":
        cost_filter = ["$$$", "$$"]
    else:
        cost_filter = ["Free", "$", "$$", "$$$"]

    start_point_name = None
    extracted_start = extracted_data.get("start_point", "None")
    if extracted_start.lower() not in ["none", "unknown"]:
        start_result = collection.query(
            query_texts=[extracted_start], n_results=1, where={"city": current_city}
        )
        if start_result["ids"][0]:
            start_point_id = start_result["ids"][0][0]
            start_point_name = start_result["metadatas"][0][0]["name"]

    results = collection.query(
        query_texts=[prompt],
        n_results=100,
        where={"$and": [{"city": current_city}, {"cost_tier": {"$in": cost_filter}}]},
    )

    locations = []
    for i in range(len(results["ids"][0])):
        meta = results["metadatas"][0][i]
        locations.append({
            "id": results["ids"][0][i],
            "name": meta["name"],
            "score": meta["importance_score"],
            "lat": meta["lat"],
            "lon": meta["lon"],
            "category": meta["category"],
            "open_time": meta.get("opening_time", "00:00"),
            "close_time": meta.get("closing_time", "23:59"),
            "desc": results["documents"][0][i],
        })

    if not locations:
        return ChatResponse(
            reply=f"I'm sorry, I don't have any locations saved for {current_city} that match your budget!",
            city=current_city,
            budget=budget_val,
            start_point_id=start_point_id,
            start_point_name=start_point_name,
            info=None,
        )

    coords = [[loc["lat"], loc["lon"]] for loc in locations]
    num_days = min(3, len(locations))
    kmeans = KMeans(n_clusters=num_days, n_init="auto", random_state=42).fit(coords)

    days_data = {i: [] for i in range(num_days)}
    for i, loc in enumerate(locations):
        days_data[kmeans.labels_[i]].append(loc)

    context_string = ""
    active_matrix = city_matrices.get(current_city, {})

    for day_index in range(num_days):
        day_locs = days_data[day_index]
        if not day_locs:
            continue

        start_loc = None
        if start_point_id:
            for idx, loc in enumerate(day_locs):
                if loc["id"] == start_point_id:
                    start_loc = day_locs.pop(idx)
                    break

        if not start_loc:
            day_locs.sort(key=lambda x: x["score"], reverse=True)
            start_loc = day_locs.pop(0)

        route = [start_loc]

        while day_locs:
            current_loc = route[-1]
            if active_matrix and current_loc["id"] in active_matrix:
                day_locs.sort(key=lambda x: active_matrix[current_loc["id"]].get(x["id"], 999999))
            else:
                day_locs.sort(
                    key=lambda x: math.hypot(current_loc["lat"] - x["lat"], current_loc["lon"] - x["lon"])
                )
            route.append(day_locs.pop(0))

        context_string += f"\n--- DAY {day_index + 1} LOCATIONS (Ordered by Walkability) ---\n"
        for step, loc in enumerate(route):
            context_string += (
                f"{step + 1}. **{loc['name']}** (Hours: {loc['open_time']} to {loc['close_time']}): {loc['desc']}\n"
            )

    system_prompt = f"""
You are an expert, hyper-personalized travel planner.
A user wants a custom itinerary. I have retrieved the best locations from our database for {current_city},
mathematically clustered them by neighborhood, and ordered them by walking distance.

CRITICAL RULES:
1. You MUST ONLY use the locations provided in the Context below.
2. You MUST NOT invent, guess, or hallucinate other places.
3. You MUST present these locations in the EXACT SEQUENTIAL ORDER they appear below for each day.
4. Do NOT repeat any locations. Each location from the context must appear at most once.

STRICT TIME & SCHEDULING RULES:
5. Assume the user's day starts at 09:00 AM. Do NOT schedule any activities before 09:00 AM.
6. Cafes MUST be recommended in the morning or early afternoon. Bars MUST be in the evening. Clubs MUST be last.
7. You MUST explicitly write the operating hours next to the scheduled time.
   Example: "**09:00 AM - 10:30 AM** (Hours: 09:00 to 17:00) | **Location Name**"
8. If your scheduled time falls outside the stated hours, shift the timeline forward until the place is open, or SKIP it.
9. ALWAYS prioritize and explicitly include any specific places or preferences the user mentioned.
10. Assume DAY TRIP category takes 7 hours starting from morning.

CONTEXT LOCATIONS:
{context_string}
"""

    api_messages = [{"role": "system", "content": system_prompt}]
    for msg in req.messages:
        api_messages.append({"role": msg.role, "content": msg.content})

    completion = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=api_messages,
        temperature=0.7,
        max_tokens=2048,
    )

    reply = completion.choices[0].message.content
    info = f"📍 {current_city} | Budget: {budget_val}"

    return ChatResponse(
        reply=reply,
        city=current_city,
        budget=budget_val,
        start_point_id=start_point_id,
        start_point_name=start_point_name,
        info=info,
    )


@app.get("/health")
def health():
    return {"status": "ok"}