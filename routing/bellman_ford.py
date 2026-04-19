from __future__ import annotations
from typing import Dict, List, Optional, Tuple
import networkx as nx
from routing.routing_table import RoutingTable, RouterId, LinkId
INF = float("inf")


def _edge_weight(graph: nx.Graph, u: RouterId, v: RouterId) -> float:
    return graph[u][v].get("weight", 1)


def _edge_link_id(graph: nx.Graph, u: RouterId, v: RouterId) -> LinkId:
    return graph[u][v].get("link_id", (u, v))


def bellman_ford_single_source(
    graph: nx.Graph,
    source: RouterId,
) -> RoutingTable:
    
    nodes: List[RouterId] = list(graph.nodes)
    n = len(nodes)

    dist: Dict[RouterId, float] = {v: INF for v in nodes}
    dist[source] = 0.0

    prev: Dict[RouterId, Optional[Tuple[RouterId, LinkId]]] = {v: None for v in nodes}

    edges: List[Tuple[RouterId, RouterId, float, LinkId]] = []
    for u, v in graph.edges():
        w    = _edge_weight(graph, u, v)
        lid  = _edge_link_id(graph, u, v)
        edges.append((u, v, w, lid))
        if not graph.is_directed():
            edges.append((v, u, w, lid))

    for _ in range(n - 1):
        updated = False
        for u, v, w, lid in edges:
            if dist[u] != INF and dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                prev[v] = (u, lid)
                updated = True
        if not updated:
            break   

    for u, v, w, _lid in edges:
        if dist[u] != INF and dist[u] + w < dist[v]:
            raise ValueError(
                f"Negative-weight cycle detected in graph (affects {u} → {v})."
            )

    rt = RoutingTable(owner_id=source)

    for dst in nodes:
        if dst == source:
            continue
        if dist[dst] == INF:
            continue  # unreachable

        node = dst
        first_hop_router: RouterId = dst
        first_hop_link: LinkId = None  

        while prev[node] is not None:
            parent, link = prev[node]
            if parent == source:
                first_hop_router = node
                first_hop_link   = link
                break
            node = parent

        rt.add_entry(dst=dst, next_hop=first_hop_router, link_id=first_hop_link)

    return rt



def compute_all_routing_tables(
    graph: nx.Graph,
) -> Dict[RouterId, RoutingTable]:
    
    return {node: bellman_ford_single_source(graph, source=node) for node in graph.nodes}



class BellmanFordRouter:

    def __init__(self, graph: nx.Graph) -> None:
        self.graph = graph
        self._tables: Dict[RouterId, RoutingTable] = {}

    def compute(self) -> Dict[RouterId, RoutingTable]:
        self._tables = compute_all_routing_tables(self.graph)
        return self._tables

    def recompute(self) -> Dict[RouterId, RoutingTable]:
        return self.compute()

    def get_table(self, router_id: RouterId) -> Optional[RoutingTable]:
        return self._tables.get(router_id)

    @property
    def tables(self) -> Dict[RouterId, RoutingTable]:
        return self._tables
