# filename: routing/dijkstra.py

"""
This File Defines the Dijkstra Routing Algorithm
Takes the full network graph and links dict.
Returns a routing table for every router. Pre-computed once at startup.
Called by network.py as: routing_algorithm(graph, links)
"""

import heapq
import logging

import networkx as nx

from routing.routing_table import RoutingTable

log = logging.getLogger(__name__)

INF = float("inf")


def _edge_weight(graph: nx.DiGraph, u: str, v: str) -> float:
    data = graph[u][v]
    
    # Check if the link object exists and is currently DOWN
    link = data.get("link")
    if link is not None and not link.is_up:
        return float('inf')  # Infinite cost so the algorithm avoids it!
        
    weight = data.get("weight", 1)
    if callable(weight):
        return weight()
    return float(weight)


def dijkstra_single_source(graph: nx.DiGraph, source: str, links: dict) -> RoutingTable:

    dist: dict = {source: 0.0}
    prev: dict = {source: None}

    heap: list = [(0.0, source)]
    visited: set = set()

    while heap:
        cost, u = heapq.heappop(heap)

        if u in visited:
            continue
        visited.add(u)

        for v in graph.neighbors(u):
            edge_cost = _edge_weight(graph, u, v)
            new_cost = cost + edge_cost

            if new_cost < dist.get(v, INF):
                dist[v] = new_cost
                prev[v] = u
                heapq.heappush(heap, (new_cost, v))

    rt = RoutingTable(router_id=source)

    for dst in dist:
        if dst == source:
            continue
        if dist[dst] == INF:
            continue

        # Walk back from dst to find the first hop after source
        node = dst
        first_hop: str = dst

        while prev[node] is not None:
            parent = prev[node]
            if parent == source:
                first_hop = node
                break
            node = parent

        link = links.get((source, first_hop))
        if link is not None:
            rt.add_route(destination=dst, next_hop=first_hop, link=link)

    return rt


def compute_all_routing_tables(graph: nx.DiGraph, links: dict) -> dict:
    tables: dict = {}
    for node in graph.nodes:
        tables[node] = dijkstra_single_source(graph, source=node, links=links)
        log.debug("Dijkstra table built for %s", node)
    return tables