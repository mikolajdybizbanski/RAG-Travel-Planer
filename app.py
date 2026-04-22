import os
import math
import json
import numpy as np
import streamlit as st
import chromadb
from sklearn.cluster import KMeans
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
st.set_page_config(page_title="Global Travel AI", page_icon="✈️", layout="centered")
st.title("AI City Travel Planner")
st.markdown("Tell me your destination, vibe, and budget, and I'll map out a perfectly routed itinerary.")

@st.cache_resource
def get_chroma_collection():
    client = chromadb.HttpClient(host="localhost", port=8000)
    return client.get_collection(name="travel_rag_collection") 

try:
    collection = get_chroma_collection()
except Exception as e:
    st.error("Error: Could not connect to ChromaDB. Is Docker running?")
    st.stop()

@st.cache_data
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

city_matrices = load_matrices()

os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
groq_client = Groq()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "target_city" not in st.session_state:
    st.session_state.target_city = None

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("E.g., Plan a 3-day trip to Prague starting at Prague Castle..."):
    
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Agents are analyzing request and mapping optimal walking routes..."):
            
            try:
                intake_prompt = f"""
                You are a strict data-extraction agent. Analyze the user's travel request and extract the parameters.
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
                    response_format={"type": "json_object"} 
                ).choices[0].message.content.strip()

                extracted_data = json.loads(extraction_response)
                
                if extracted_data.get("city") != "Unknown":
                    st.session_state.target_city = extracted_data["city"]
                    target_city = extracted_data["city"]
                else:
                    if st.session_state.target_city is not None:
                        target_city = st.session_state.target_city
                    else:
                        msg = "I couldn't tell which city you want to visit! Could you please specify?"
                        st.markdown(msg)
                        st.session_state.messages.append({"role": "assistant", "content": msg})
                        st.stop()

                budget_val = extracted_data.get("budget", "Unknown")
                if budget_val == "OnlyFreePlaces": cost_filter = ["Free"]
                elif budget_val == "LimitedBudget": cost_filter = ["$", "Free"]
                elif budget_val == "MostPlacesAllowed": cost_filter = ["Free", "$", "$$"]
                elif budget_val == "OnlyHighEndPlaces": cost_filter = ["$$$", "$$"]
                else: cost_filter = ["Free", "$", "$$", "$$$"]

                requested_start_id = None
                requested_start = extracted_data.get("start_point", "None")
                if requested_start.lower() != "none" and requested_start.lower() != "unknown":
                    start_result = collection.query(
                        query_texts=[requested_start], n_results=1, where={"city": target_city}
                    )
                    if start_result['ids'][0]:
                        requested_start_id = start_result['ids'][0][0]
                        st.info(f"Start Point: **{start_result['metadatas'][0][0]['name']}**")
                
                st.info(f"📍 **{target_city}**")
                st.info(f"Budget: **{budget_val}**")

                results = collection.query(
                    query_texts=[prompt],
                    n_results=100, 
                    where={"$and": [
                        {"city": target_city},
                        {"cost_tier": {"$in": cost_filter}}
                    ]}
                )

                locations = []
                for i in range(len(results['ids'][0])):
                    meta = results['metadatas'][0][i]
                    locations.append({
                        "id": results['ids'][0][i], 
                        "name": meta['name'],
                        "score": meta['importance_score'],
                        "lat": meta['lat'],
                        "lon": meta['lon'],
                        "category": meta['category'],
                        "open_time": meta.get('opening_time', '00:00'),
                        "close_time": meta.get('closing_time', '23:59'),
                        "desc": results['documents'][0][i]
                    })
                
                if len(locations) == 0:
                    msg = f"I'm sorry, I don't have any locations saved in my database for {target_city} that match your budget!"
                    st.markdown(msg)
                    st.session_state.messages.append({"role": "assistant", "content": msg})
                    st.stop()

                coords = [[loc['lat'], loc['lon']] for loc in locations]
                num_days = min(3, len(locations)) 
                kmeans = KMeans(n_clusters=num_days, n_init="auto", random_state=42).fit(coords)

                days_data = {i: [] for i in range(num_days)}
                for i, loc in enumerate(locations):
                    days_data[kmeans.labels_[i]].append(loc)

                context_string = ""
                active_matrix = city_matrices.get(target_city, {})
                
                for day_index in range(num_days):
                    day_locs = days_data[day_index]
                    if not day_locs:
                        continue
                    
                    start_loc = None
                    if requested_start_id:
                        for idx, loc in enumerate(day_locs):
                            if loc['id'] == requested_start_id:
                                start_loc = day_locs.pop(idx) 
                                break
                    
                    if not start_loc:
                        day_locs.sort(key=lambda x: x['score'], reverse=True)
                        start_loc = day_locs.pop(0)
                        
                    route = [start_loc] 
                    
                    while len(day_locs) > 0:
                        current_loc = route[-1]
                        
                        if active_matrix and current_loc['id'] in active_matrix:
                            day_locs.sort(key=lambda x: active_matrix[current_loc['id']].get(x['id'], 999999))
                        else:
                            day_locs.sort(key=lambda x: math.hypot(current_loc['lat'] - x['lat'], current_loc['lon'] - x['lon']))
                        
                        route.append(day_locs.pop(0))
                    
                    context_string += f"\n--- DAY {day_index + 1} LOCATIONS (Ordered by Walkability) ---\n"
                    for step, loc in enumerate(route):
                        context_string += f"{step + 1}. **{loc['name']}** (Hours: {loc['open_time']} to {loc['close_time']}): {loc['desc']}\n"

                system_prompt = f"""
                You are an expert, hyper-personalized travel planner. 
                A user wants a custom itinerary. I have retrieved the best locations from our database for {target_city}, mathematically clustered them by neighborhood, and ordered them by walking distance.

                CRITICAL RULES:
                1. You MUST ONLY use the locations provided in the Context below. 
                2. You MUST NOT invent, guess, or hallucinate other places.
                3. You MUST present these locations in the EXACT SEQUENTIAL ORDER they appear below for each day.
                4. Do NOT repeat any locations. Each location from the context must appear at most once.
                
                STRICT TIME & SCHEDULING RULES:
                5. Assume the user's day starts at 09:00 AM. Do NOT schedule any activities before 09:00 AM.
                6. Cafe's MUST be recommended in the morning or early afternoon. Bars MUST be in the evening. Clubs MUST be the last attraction for the day.
                7. You MUST explicitly write the operating hours next to the scheduled time to prove it is valid. Example: "**09:00 AM - 10:30 AM** (Hours: 09:00 to 17:00) | **Location Name**"
                8. If your scheduled time falls outside the stated hours, or conflicts with Rule 6, you MUST shift the timeline forward until the place is open, or SKIP the location entirely.
                9. ALWAYS prioritize and explicitly include any specific places or preferences the user mentioned in their request.

                CONTEXT LOCATIONS:
                {context_string}
                """

                api_messages = [{"role": "system", "content": system_prompt}]

                for msg in st.session_state.messages:
                    api_messages.append({"role": msg["role"], "content": msg["content"]})

                completion = groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=api_messages,
                    temperature=0.7, 
                    max_tokens=2048
                )
                
                response = completion.choices[0].message.content
                
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            
            except Exception as e:
                st.error(f"An error occurred: {e}")