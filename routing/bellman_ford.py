# filename: routing/bellman_ford.py

"""
This File Defines the Bellman-Ford Routing Algorithm
Distance-vector algorithm. Re-runs when a LinkFailureEvent fires in SimPy.
Allows dynamic rerouting — if a link goes down mid-simulation, packets find a new path.
Called by network.py as: routing_algorithm(graph, links)
"""

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
        return float("inf")  # Infinite cost so the algorithm avoids it!

    weight = data.get("weight", 1)
    if callable(weight):
        return weight()
    return float(weight)


def bellman_ford_single_source(
    graph: nx.DiGraph, source: str, links: dict
) -> RoutingTable:

    nodes: list = list(graph.nodes)
    n = len(nodes)

    dist: dict = {v: INF for v in nodes}
    dist[source] = 0.0

    prev: dict = {v: None for v in nodes}

    edges: list = []
    for u, v in graph.edges():
        w = _edge_weight(graph, u, v)
        edges.append((u, v, w))

    for _ in range(n - 1):
        updated = False
        for u, v, w in edges:
            if dist[u] != INF and dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                prev[v] = u
                updated = True
        if not updated:
            break

    for u, v, w in edges:
        if dist[u] != INF and dist[u] + w < dist[v]:
            raise ValueError(
                f"Negative-weight cycle detected in graph (affects {u} -> {v})."
            )

    rt = RoutingTable(router_id=source)

    for dst in nodes:
        if dst == source:
            continue
        if dist[dst] == INF:
            continue

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
        tables[node] = bellman_ford_single_source(graph, source=node, links=links)
        log.debug("Bellman-Ford table built for %s", node)
    return tables
