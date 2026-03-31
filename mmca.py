import streamlit as st
import pulp
import networkx as nx
import osmnx as ox
import matplotlib.pyplot as plt
import numpy as np
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

# -----------------------------
# Optimizer Class (same logic)
# -----------------------------
class EcommerceDeliveryOptimizer:
    def __init__(self, warehouse_coords, hub_coords):
        self.warehouse = (0, warehouse_coords)
        self.hubs = [(i+1, coord) for i, coord in enumerate(hub_coords)]
        self.G = self._build_road_network()

    def _get_bbox(self):
        lats = [self.warehouse[1][0]] + [c[0] for _, c in self.hubs]
        lons = [self.warehouse[1][1]] + [c[1] for _, c in self.hubs]
        return (max(lats)+0.01, min(lats)-0.01, max(lons)+0.01, min(lons)-0.01)

    def _build_road_network(self):
        bbox = self._get_bbox()
        return ox.graph_from_bbox(*bbox, network_type='drive')

    def _calculate_distances(self):
        locations = [self.warehouse[1]] + [c for _, c in self.hubs]
        dist_matrix = {}

        for i, start in enumerate(locations):
            for j, end in enumerate(locations):
                try:
                    orig = ox.distance.nearest_nodes(self.G, start[1], start[0])
                    dest = ox.distance.nearest_nodes(self.G, end[1], end[0])
                    path = nx.shortest_path(self.G, orig, dest, weight='length')
                    dist_matrix[(i, j)] = nx.path_weight(self.G, path, 'length')
                except:
                    dist_matrix[(i, j)] = 10000
        return dist_matrix

    def solve_flow_model(self, demands):
        model = pulp.LpProblem("Delivery_Flow", pulp.LpMinimize)

        flow = pulp.LpVariable.dicts("flow",
                                    [(0, j) for j, _ in self.hubs],
                                    lowBound=0)

        distances = self._calculate_distances()

        model += pulp.lpSum(distances[(0, j)] * flow[(0, j)]
                            for j, _ in self.hubs)

        for j, _ in self.hubs:
            model += flow[(0, j)] == demands[j-1]

        model.solve(pulp.PULP_CBC_CMD(msg=0))

        return {j: flow[(0, j)].varValue for j, _ in self.hubs}

    def solve_vrp(self, demands, vehicle_capacity=100, num_vehicles=3):
        depot = 0
        locations = [self.warehouse[1]] + [coord for _, coord in self.hubs]
        distance_matrix = self._calculate_distances()

        manager = pywrapcp.RoutingIndexManager(len(locations), num_vehicles, depot)
        routing = pywrapcp.RoutingModel(manager)

        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return int(distance_matrix[(from_node, to_node)])

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        def demand_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            return demands[from_node-1] if from_node > 0 else 0

        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)

        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,
            [vehicle_capacity] * num_vehicles,
            True,
            'Capacity'
        )

        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )

        solution = routing.SolveWithParameters(search_parameters)

        return self._extract_solution(routing, solution, manager)

    def _extract_solution(self, routing, solution, manager):
        routes = []
        if solution:
            for vehicle_id in range(routing.vehicles()):
                index = routing.Start(vehicle_id)
                route = []
                while not routing.IsEnd(index):
                    node = manager.IndexToNode(index)
                    route.append(node)
                    index = solution.Value(routing.NextVar(index))
                routes.append(route)
        return routes


# -----------------------------
# Plot Function
# -----------------------------
def plot_routes(routes, hub_coords, warehouse):
    fig, ax = plt.subplots(figsize=(10, 6))

    colors = plt.cm.Set3(np.linspace(0, 1, len(routes)))

    for i, route in enumerate(routes):
        coords = []
        for node in route:
            if node == 0:
                coords.append(warehouse)
            else:
                coords.append(hub_coords[node-1])

        if len(coords) > 1:
            ax.plot(*zip(*coords), color=colors[i], label=f'Vehicle {i+1}')

    # Plot hubs
    ax.scatter(*zip(*hub_coords), c='red', s=80, label='Hubs')
    ax.scatter(*warehouse, c='green', s=150, marker='^', label='Warehouse')

    ax.legend()
    ax.set_title("Optimized Routes")
    ax.grid(True)

    return fig


# -----------------------------
# Streamlit UI
# -----------------------------
st.title("🚚 Ecommerce Delivery Optimizer")

st.sidebar.header("Input Data")

warehouse_lat = st.sidebar.number_input("Warehouse Latitude", value=19.0760)
warehouse_lon = st.sidebar.number_input("Warehouse Longitude", value=72.8777)

num_hubs = st.sidebar.slider("Number of Hubs", 1, 10, 3)

hub_coords = []
demands = []

st.sidebar.subheader("Hub Details")

for i in range(num_hubs):
    lat = st.sidebar.number_input(f"Hub {i+1} Lat", value=19.1 + i*0.01, key=f"lat{i}")
    lon = st.sidebar.number_input(f"Hub {i+1} Lon", value=72.8 + i*0.01, key=f"lon{i}")
    demand = st.sidebar.number_input(f"Demand {i+1}", value=10, key=f"d{i}")

    hub_coords.append((lat, lon))
    demands.append(demand)

vehicle_capacity = st.sidebar.number_input("Vehicle Capacity", value=50)
num_vehicles = st.sidebar.slider("Number of Vehicles", 1, 5, 2)

if st.button("Run Optimization"):
    with st.spinner("Optimizing routes..."):
        optimizer = EcommerceDeliveryOptimizer(
            (warehouse_lat, warehouse_lon),
            hub_coords
        )

        flow = optimizer.solve_flow_model(demands)
        routes = optimizer.solve_vrp(demands, vehicle_capacity, num_vehicles)

        st.subheader("Flow Allocation")
        st.write(flow)

        st.subheader("Routes")
        st.write(routes)

        fig = plot_routes(routes, hub_coords, (warehouse_lat, warehouse_lon))
        st.pyplot(fig)