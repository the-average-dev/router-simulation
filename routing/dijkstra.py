from __future__ import annotations
import heapq
from typing import Any, Dict, Hashable, Optional
import networkx as nx
from routing.routing_table import RoutingTable, RouterId, LinkId, build_routing_tables
INF = float("inf")


def edge_weight(graph: nx.Graph, u: RouterId, v: RouterId) -> float:
    return graph[u][v].get("weight", 1)


def edge_linkid(graph: nx.Graph, u: RouterId, v: RouterId) -> LinkId:
    return graph[u][v].get("link_id", (u, v))


def dijkstra_single_source(
    graph: nx.Graph,
    source: RouterId,
) -> RoutingTable:
    
    
    dist: Dict[RouterId, float] = {source: 0.0}
    prev: Dict[RouterId, Optional[tuple]] = {source: None}

    heap: list[tuple[float, Any]] = [(0.0, source)]

    visited: set[RouterId] = set()

    while heap:
        cost, u = heapq.heappop(heap)

        if u in visited:
            continue
        visited.add(u)

        for v in graph.neighbors(u):
            edge_cost = edge_weight(graph, u, v)
            link_id   = edge_linkid(graph, u, v)
            new_cost  = cost + edge_cost

            if new_cost < dist.get(v, INF):
                dist[v] = new_cost
                prev[v] = (u, link_id)
                heapq.heappush(heap, (new_cost, v))


    rt = RoutingTable(owner_id=source)

    for dst in dist:
        if dst == source:
            continue
        if dist[dst] == INF:
            continue  

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
    
    tables: Dict[RouterId, RoutingTable] = {}
    for node in graph.nodes:
        tables[node] = dijkstra_single_source(graph, source=node)
    return tables
