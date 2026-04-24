# viz/plot_topology.py

import os
import logging
import matplotlib.pyplot as plt
import networkx as nx
from core.network import Network

logger = logging.getLogger(__name__)

class TopologyPlotter:
    def __init__(self, network: Network, out_dir="graphs",seed = 42):
        self.network = network
        self.out_dir = out_dir
        self.seed = seed
        os.makedirs(self.out_dir, exist_ok=True)

    def plot(self):
        graph = self.network.graph
        
        if len(graph.nodes) == 0:
            logger.debug("No nodes in graph to plot.")
            return

        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Use a spring layout for nice visual spacing
        pos = nx.spring_layout(graph, seed=self.seed, weight=None)

        # Draw nodes
        nx.draw_networkx_nodes(
            graph, pos, 
            ax=ax, 
            node_color='lightblue', 
            node_size=800, 
            edgecolors='black'
        )

        # Draw edges
        nx.draw_networkx_edges(
            graph, pos, 
            ax=ax, 
            edge_color='gray', 
            arrows=True, 
            arrowsize=15
        )

        # Draw labels
        nx.draw_networkx_labels(
            graph, pos, 
            ax=ax, 
            font_size=12, 
            font_family="sans-serif",
            font_weight="bold"
        )

        ax.set_title("Network Topology Map", fontsize=14, pad=15)
        ax.axis('off') # Hide the axis grid for the map

        filepath = os.path.join(self.out_dir, "network_topology.png")
        plt.savefig(filepath, bbox_inches="tight", dpi=150)
        logger.info(f"Saved graph: {filepath}")
        plt.close(fig)