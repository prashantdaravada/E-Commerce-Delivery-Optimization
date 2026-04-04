import streamlit as st
import requests
import heapq
import time

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(page_title="Delivery Optimizer", layout="centered")

st.title("🚚 E-Commerce Delivery Optimization")
st.write("Optimize delivery routes using real-time Google Maps data")

# -------------------------------
# USER INPUT
# -------------------------------
api_key = st.text_input("Enter Google Maps API Key", type="password")

warehouse = st.text_input("Warehouse Location", "Mumbai, India")

hubs_input = st.text_area(
    "Enter Hub Locations (one per line)",
    "Thane, India\nNavi Mumbai, India\nPune, India"
)

hubs = [h.strip() for h in hubs_input.split("\n") if h.strip()]

# -------------------------------
# API FUNCTION
# -------------------------------
def get_distance_time(origin, destination, api_key):
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"

    params = {
        "origins": origin,
        "destinations": destination,
        "key": api_key,
        "departure_time": "now"
    }

    response = requests.get(url, params=params)
    data = response.json()

    try:
        element = data['rows'][0]['elements'][0]
        return element['distance']['value'], element['duration']['value']
    except:
        return float('inf'), float('inf')

# -------------------------------
# BUILD GRAPH
# -------------------------------
def build_graph(locations, api_key):
    graph = {}

    progress = st.progress(0)
    total = len(locations) * (len(locations) - 1)
    count = 0

    for origin in locations:
        graph[origin] = {}
        for destination in locations:
            if origin != destination:
                dist, time_sec = get_distance_time(
                    locations[origin],
                    locations[destination],
                    api_key
                )
                graph[origin][destination] = time_sec

                count += 1
                progress.progress(count / total)
                time.sleep(0.5)

    return graph

# -------------------------------
# DIJKSTRA
# -------------------------------
def dijkstra(graph, start):
    pq = [(0, start)]
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    previous = {node: None for node in graph}

    while pq:
        current_distance, current_node = heapq.heappop(pq)

        for neighbor, weight in graph[current_node].items():
            distance = current_distance + weight

            if distance < distances[neighbor]:
                distances[neighbor] = distance
                previous[neighbor] = current_node
                heapq.heappush(pq, (distance, neighbor))

    return distances, previous

# -------------------------------
# PATH
# -------------------------------
def get_path(previous, start, end):
    path = []
    while end:
        path.insert(0, end)
        end = previous[end]
    return path

# -------------------------------
# RUN BUTTON
# -------------------------------
if st.button("Optimize Routes"):
    if not api_key:
        st.error("Please enter API Key")
    else:
        st.info("Building graph using real-time data...")

        locations = {"Warehouse": warehouse}
        for i, hub in enumerate(hubs):
            locations[f"Hub{i+1}"] = hub

        graph = build_graph(locations, api_key)

        st.info("Optimizing routes...")

        distances, previous = dijkstra(graph, "Warehouse")

        st.success("Optimization Complete ✅")

        # -------------------------------
        # RESULTS
        # -------------------------------
        for hub in locations:
            if hub != "Warehouse":
                path = get_path(previous, "Warehouse", hub)
                time_minutes = distances[hub] / 60

                st.subheader(f"📍 Route to {hub}")
                st.write(" → ".join(path))
                st.write(f"⏱ Time: {time_minutes:.2f} minutes")
