import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from networkx.algorithms import community

st.set_page_config(page_title="Fan Network Analysis", layout="wide")

st.title("🎬 Entertainment Fan Network Analysis")
st.write("Graph-Based Community Detection & Influencer Ranking")

# -----------------------------
# FUNCTION: Analyze Graph
# -----------------------------
def analyze_graph(G):

    # Centrality Measures
    degree = nx.degree_centrality(G)
    betweenness = nx.betweenness_centrality(G)
    eigenvector = nx.eigenvector_centrality(G, max_iter=1000)

    # DataFrame
    df = pd.DataFrame({
        "Fan": list(degree.keys()),
        "Degree": list(degree.values()),
        "Betweenness": list(betweenness.values()),
        "Eigenvector": list(eigenvector.values())
    })

    # Top influencers
    top_degree = max(degree, key=degree.get)
    top_between = max(betweenness, key=betweenness.get)
    top_eigen = max(eigenvector, key=eigenvector.get)

    return df, top_degree, top_between, top_eigen


# -----------------------------
# SCENARIO SELECTION
# -----------------------------
scenario = st.sidebar.selectbox(
    "Select Network Scenario",
    ["Clustered Network", "Star Network"]
)

# -----------------------------
# BUILD GRAPH
# -----------------------------
fans = ["A","B","C","D","E","F","G","H"]

if scenario == "Clustered Network":
    G = nx.Graph()
    edges = [("A","B"), ("A","C"), ("B","C"), ("B","D"),
             ("C","E"), ("E","F"), ("F","G"), ("G","H"), ("F","H")]
    title = "Clustered Fan Network"

else:
    G = nx.Graph()
    edges = [("A","B"), ("A","C"), ("A","D"),
             ("A","E"), ("A","F"), ("A","G"), ("A","H")]
    title = "Star Fan Network"

G.add_nodes_from(fans)
G.add_edges_from(edges)

# -----------------------------
# ANALYSIS
# -----------------------------
df, top_degree, top_between, top_eigen = analyze_graph(G)

# -----------------------------
# DISPLAY RESULTS
# -----------------------------
st.subheader("📊 Centrality Metrics")
st.dataframe(df)

col1, col2, col3 = st.columns(3)

col1.metric("Top Degree Influencer", top_degree)
col2.metric("Top Betweenness Influencer", top_between)
col3.metric("Top Eigenvector Influencer", top_eigen)

# -----------------------------
# COMMUNITY DETECTION
# -----------------------------
st.subheader("👥 Community Detection (Girvan-Newman)")

comp = community.girvan_newman(G)
first_level = next(comp)
communities = [list(c) for c in first_level]

st.write("Detected Communities:", communities)

# -----------------------------
# GRAPH VISUALIZATION
# -----------------------------
st.subheader("🌐 Network Graph")

fig, ax = plt.subplots()
pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True, ax=ax)
st.pyplot(fig)

# -----------------------------
# CENTRALITY CHART
# -----------------------------
st.subheader("📈 Centrality Comparison")

fig2, ax2 = plt.subplots()
df.set_index("Fan").plot(kind="bar", ax=ax2)
st.pyplot(fig2)

# -----------------------------
# INSIGHTS
# -----------------------------
st.subheader("🧠 Insights")

if scenario == "Clustered Network":
    st.write("""
    - Two communities are visible.
    - Bridge nodes have high betweenness.
    - Network is more stable and decentralized.
    """)
else:
    st.write("""
    - One central influencer dominates.
    - Network is highly centralized.
    - Removing the hub disconnects the network.
    """)
