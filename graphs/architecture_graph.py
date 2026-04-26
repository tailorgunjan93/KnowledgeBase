"""Architecture Graph Generator for RAG Application."""

import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


def create_rag_architecture_graph():
    """Create a visual graph of the RAG application architecture."""

    G = nx.DiGraph()

    # Define nodes with labels and colors
    nodes = [
        # Frontend
        ("Frontend", "lightblue"),
        ("Login/Signup", "lightyellow"),
        ("Chat UI", "lightyellow"),
        ("KB Manager", "lightyellow"),
        ("Summarizer", "lightyellow"),
        ("Settings", "lightyellow"),
        # Backend
        ("FastAPI", "lightgreen"),
        ("Auth API", "lightgreen"),
        ("KB API", "lightgreen"),
        ("Chat API", "lightgreen"),
        ("Summarize API", "lightgreen"),
        # LangGraph
        ("IntentEvaluator", "salmon"),
        ("QueryEvaluator", "salmon"),
        ("ResultEvaluator", "salmon"),
        # Search
        ("FAISS Store", "orange"),
        ("BM25 Store", "orange"),
        ("Hybrid Search", "orange"),
        # Storage
        ("SQLite DB", "lightgray"),
        ("FAISS Indices", "lightgray"),
        # External
        ("Groq LLM", "violet"),
        ("Web Search", "violet"),
        ("Sentence Transformers", "violet"),
    ]

    for node, color in nodes:
        G.add_node(node, color=color)

    # Define edges
    edges = [
        # Frontend to Backend
        ("Frontend", "FastAPI"),
        ("Login/Signup", "Auth API"),
        ("Chat UI", "Chat API"),
        ("KB Manager", "KB API"),
        ("Summarizer", "Summarize API"),
        # Backend connections
        ("Auth API", "SQLite DB"),
        ("KB API", "SQLite DB"),
        ("Chat API", "IntentEvaluator"),
        # LangGraph flow
        ("IntentEvaluator", "QueryEvaluator"),
        ("QueryEvaluator", "ResultEvaluator"),
        # Search flow
        ("QueryEvaluator", "Hybrid Search"),
        ("Hybrid Search", "FAISS Store"),
        ("Hybrid Search", "BM25 Store"),
        # External services
        ("Chat API", "Groq LLM"),
        ("ResultEvaluator", "Groq LLM"),
        ("Chat API", "Web Search"),
        ("QueryEvaluator", "Sentence Transformers"),
    ]

    G.add_edges_from(edges)

    return G


def draw_graph(output_path="architecture_graph.png"):
    """Draw and save the architecture graph."""

    G = create_rag_architecture_graph()

    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(20, 16))
    ax.set_title("RAG Application Architecture", fontsize=16, fontweight="bold")

    # Define positions manually for better layout
    pos = {
        # Frontend layer (top)
        "Frontend": (0.5, 0.95),
        "Login/Signup": (0.1, 0.85),
        "Chat UI": (0.35, 0.85),
        "KB Manager": (0.65, 0.85),
        "Summarizer": (0.9, 0.85),
        "Settings": (0.9, 0.75),
        # Backend layer
        "FastAPI": (0.5, 0.65),
        "Auth API": (0.1, 0.55),
        "KB API": (0.35, 0.55),
        "Chat API": (0.5, 0.55),
        "Summarize API": (0.9, 0.55),
        # LangGraph layer
        "IntentEvaluator": (0.2, 0.4),
        "QueryEvaluator": (0.4, 0.4),
        "ResultEvaluator": (0.6, 0.4),
        # Search layer
        "Hybrid Search": (0.4, 0.25),
        "FAISS Store": (0.2, 0.15),
        "BM25 Store": (0.6, 0.15),
        # Storage & External (bottom)
        "SQLite DB": (0.1, 0.05),
        "Groq LLM": (0.8, 0.05),
        "Web Search": (0.5, 0.05),
        "Sentence Transformers": (0.65, 0.25),
        "FAISS Indices": (0.35, 0.15),
    }

    # Get colors for nodes
    colors = []
    for node in G.nodes():
        color = G.nodes[node].get("color", "lightblue")
        colors.append(color)

    # Draw
    nx.draw(
        G,
        pos,
        ax=ax,
        with_labels=True,
        node_color=colors,
        node_size=3000,
        font_size=8,
        font_weight="bold",
        edge_color="gray",
        arrows=True,
        arrowsize=15,
        connectionstyle="arc3,rad=0.1",
    )

    # Add legend
    legend_elements = [
        mpatches.Patch(color="lightblue", label="Frontend"),
        mpatches.Patch(color="lightgreen", label="Backend API"),
        mpatches.Patch(color="salmon", label="LangGraph Nodes"),
        mpatches.Patch(color="orange", label="Search Engine"),
        mpatches.Patch(color="lightgray", label="Storage"),
        mpatches.Patch(color="violet", label="External Services"),
    ]
    ax.legend(handles=legend_elements, loc="lower left", fontsize=10)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Graph saved to {output_path}")
    plt.close()


def create_data_flow_graph():
    """Create a data flow graph showing how a query moves through the system."""

    G = nx.DiGraph()

    # Add nodes
    nodes = [
        ("User Query", "lightblue"),
        ("Intent Detection", "salmon"),
        ("Query Refinement", "salmon"),
        ("Hybrid Search", "orange"),
        ("FAISS Search", "orange"),
        ("BM25 Search", "orange"),
        ("Result Ranking", "orange"),
        ("Source Context", "lightgreen"),
        ("LLM Generation", "violet"),
        ("Result Validation", "salmon"),
        ("Final Answer", "lightblue"),
    ]

    for node, color in nodes:
        G.add_node(node, color=color)

    # Add edges showing data flow
    edges = [
        ("User Query", "Intent Detection"),
        ("Intent Detection", "Query Refinement"),
        ("Query Refinement", "Hybrid Search"),
        ("Hybrid Search", "FAISS Search"),
        ("Hybrid Search", "BM25 Search"),
        ("FAISS Search", "Result Ranking"),
        ("BM25 Search", "Result Ranking"),
        ("Result Ranking", "Source Context"),
        ("Source Context", "LLM Generation"),
        ("LLM Generation", "Result Validation"),
        ("Result Validation", "Final Answer"),
    ]

    G.add_edges_from(edges)

    return G


def draw_data_flow(output_path="data_flow_graph.png"):
    """Draw and save the data flow graph."""

    G = create_data_flow_graph()

    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    ax.set_title("RAG Pipeline Data Flow", fontsize=16, fontweight="bold")

    pos = {
        "User Query": (0.5, 0.95),
        "Intent Detection": (0.5, 0.85),
        "Query Refinement": (0.5, 0.75),
        "Hybrid Search": (0.5, 0.65),
        "FAISS Search": (0.2, 0.55),
        "BM25 Search": (0.8, 0.55),
        "Result Ranking": (0.5, 0.45),
        "Source Context": (0.5, 0.35),
        "LLM Generation": (0.5, 0.25),
        "Result Validation": (0.5, 0.15),
        "Final Answer": (0.5, 0.05),
    }

    colors = [G.nodes[n].get("color", "lightblue") for n in G.nodes()]

    nx.draw(
        G,
        pos,
        ax=ax,
        with_labels=True,
        node_color=colors,
        node_size=4000,
        font_size=9,
        font_weight="bold",
        edge_color="green",
        arrows=True,
        arrowsize=20,
        connectionstyle="arc3,rad=0.1",
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Data flow graph saved to {output_path}")
    plt.close()


if __name__ == "__main__":
    # Generate both graphs
    draw_graph("architecture_graph.png")
    draw_data_flow("data_flow_graph.png")
    print("Done! Check the generated PNG files.")
