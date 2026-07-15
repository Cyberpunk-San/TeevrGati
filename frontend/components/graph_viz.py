import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt

def render_graph_viz(kg, active_asset_id: str):
    """
    Renders a dark-themed matplotlib sub-graph around the active asset node,
    highlighting the self-healing operations (outdated nodes turn gray, REPLACED_BY links turn green/dashed).
    """
    st.markdown("### 🕸️ Live Self-Healing Knowledge Graph Ontology")
    
    # 1. Filter nodes related to the active asset tag (e.g. "P-201")
    target_node = f"EQ_{active_asset_id}"
    
    # Extract sub-graph (immediate neighbors and nodes with connections)
    nodes_to_include = {target_node} if target_node in kg.graph.nodes else set()
    
    # Get 1-hop and 2-hop neighbors
    for u, v, data in kg.graph.edges(data=True):
        if u == target_node or v == target_node:
            nodes_to_include.add(u)
            nodes_to_include.add(v)
            
    # Include all REPLACED_BY links in the entire graph so self-healing is always visible!
    for u, v, data in kg.graph.edges(data=True):
        if data.get('relation') == 'REPLACED_BY':
            nodes_to_include.add(u)
            nodes_to_include.add(v)
            
    if not nodes_to_include:
        # Fallback to top 15 nodes in the graph if no active asset is loaded
        nodes_to_include = list(kg.graph.nodes)[:15]
        
    subgraph = kg.graph.subgraph(nodes_to_include)
    
    if len(subgraph) == 0:
        st.info("No nodes in the knowledge graph to visualize yet.")
        return
        
    # Create matplotlib figure with dark background
    fig, ax = plt.subplots(figsize=(10, 6), facecolor='#1a1f2c')
    ax.set_facecolor('#1a1f2c')
    
    # Positions layout
    pos = nx.spring_layout(subgraph, k=1.2, seed=42)
    
    # Determine node colors, labels, and sizes
    node_colors = []
    node_labels = {}
    node_sizes = []
    
    for node, data in subgraph.nodes(data=True):
        node_type = data.get('type', 'Unknown')
        status = data.get('status', 'active')
        
        # Color mapping
        if status == 'outdated':
            color = '#4a4e69'  # Dim gray
        elif node_type == 'EQUIPMENT':
            color = '#00f5d4'  # Neon Cyan
        elif node_type == 'DOCUMENT':
            color = '#4cc9f0'  # Sky Blue
        elif node_type == 'TACIT_RULE':
            color = '#52b788'  # Emerald Green
        elif node_type == 'REGULATION':
            color = '#f77f00'  # Gold
        elif node_type == 'PERSON':
            color = '#f72585'  # Neon Pink
        else:
            color = '#8e9aaf'  # Cool Gray
            
        node_colors.append(color)
        
        # Label formatting
        label = data.get('tag') or data.get('name') or data.get('reference') or node
        if status == 'outdated':
            label = f"[OUTDATED]\n{label.split('.')[0] if '.' in label else label}"
        elif node_type == 'TACIT_RULE':
            label = f"💡 Tacit Rule\n\"{label[:15]}...\""
        node_labels[node] = label
        
        # Size mapping
        size = 1200 if node == target_node else 800
        node_sizes.append(size)
        
    # Draw nodes
    nx.draw_networkx_nodes(
        subgraph, pos, ax=ax,
        node_color=node_colors,
        node_size=node_sizes,
        edgecolors='#2e374a',
        linewidths=1.5
    )
    
    # Draw edges separated by type
    replaced_edges = []
    standard_edges = []
    
    for u, v, key, data in subgraph.edges(keys=True, data=True):
        if data.get('relation') == 'REPLACED_BY':
            replaced_edges.append((u, v))
        else:
            standard_edges.append((u, v))
            
    # Standard edges (solid grey)
    nx.draw_networkx_edges(
        subgraph, pos, ax=ax,
        edgelist=standard_edges,
        edge_color='#5c677d',
        width=1.2,
        arrowsize=12,
        arrows=True
    )
    
    # Self-healing REPLACED_BY edges (dashed neon green)
    nx.draw_networkx_edges(
        subgraph, pos, ax=ax,
        edgelist=replaced_edges,
        edge_color='#52b788',
        width=2.5,
        style='--',
        arrowsize=15,
        arrows=True
    )
    
    # Draw labels
    nx.draw_networkx_labels(
        subgraph, pos, ax=ax,
        labels=node_labels,
        font_size=8,
        font_color='white',
        font_family='sans-serif',
        font_weight='bold'
    )
    
    # Add edge labels for REPLACED_BY
    edge_labels = {}
    for u, v, data in subgraph.edges(data=True):
        if data.get('relation') == 'REPLACED_BY':
            edge_labels[(u, v)] = "REPLACED_BY"
            
    nx.draw_networkx_edge_labels(
        subgraph, pos, ax=ax,
        edge_labels=edge_labels,
        font_size=7,
        font_color='#52b788',
        font_weight='bold',
        bbox=dict(facecolor='#1a1f2c', edgecolor='none', alpha=0.8)
    )
    
    # Hide axes
    ax.axis('off')
    
    # Display in Streamlit
    st.pyplot(fig, clear_figure=True)
    
    # Color Legend
    st.markdown("""
    <div style="display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; margin-top: 10px; font-size: 0.85rem;">
        <span style="color: #00f5d4; font-weight: bold;">● Equipment</span>
        <span style="color: #4cc9f0; font-weight: bold;">● Active SOP</span>
        <span style="color: #52b788; font-weight: bold;">● Tacit Rule / Winner</span>
        <span style="color: #f72585; font-weight: bold;">● Personnel</span>
        <span style="color: #4a4e69; font-weight: bold;">● Outdated/Superseded</span>
        <span style="color: #52b788; font-weight: bold;">--→ Replaced Link</span>
    </div>
    """, unsafe_allow_html=True)
