"""
routing/dijkstra.py
===================
Static shortest-path routing via Dijkstra's algorithm.

Input
-----
A networkx graph where:
    * Nodes are router ids (any hashable).
    * Edges carry a 'weight' attribute (link cost / delay / hop-count).
      If 'weight' is absent, it defaults to 1 (equal-cost / hop-count routing).
    * Edges carry a 'link_id' attribute identifying the SimPy link resource.
      If absent, a tuple (u, v) is used as the link id.

Output
------
    {router_id: RoutingTable}

One RoutingTable per router, fully populated with next-hop entries to every
other reachable router in the graph.

Algorithm
---------
Standard Dijkstra with a min-heap (priority queue).  Runs once per router
(single-source).  Total complexity: O(R * (E + R) log R) where R = routers,
E = edges — fast enough for any realistic lab topology.

No SimPy. No core/ imports. Uses networkx only for graph traversal.
"""

from __future__ import annotations

import heapq
from typing import Any, Dict, Hashable, Optional

import networkx as nx

from routing.routing_table import RoutingTable, RouterId, LinkId, build_routing_tables

# Sentinel for "unreachable"
INF = float("inf")


def _edge_weight(graph: nx.Graph, u: RouterId, v: RouterId) -> float:
    """Return the weight of edge (u, v), defaulting to 1."""
    return graph[u][v].get("weight", 1)


def _edge_link_id(graph: nx.Graph, u: RouterId, v: RouterId) -> LinkId:
    """Return the link_id of edge (u, v), defaulting to (u, v) tuple."""
    return graph[u][v].get("link_id", (u, v))


def dijkstra_single_source(
    graph: nx.Graph,
    source: RouterId,
) -> RoutingTable:
    """
    Run Dijkstra from *source* and return its RoutingTable.

    Parameters
    ----------
    graph  : networkx.Graph (or DiGraph) with optional 'weight' / 'link_id' edge attrs.
    source : router id to compute paths from.

    Returns
    -------
    RoutingTable
        Entries for every reachable destination, with the correct next-hop
        and outgoing link from *source*.
    """
    # dist[v]     = best known cost from source to v
    # prev[v]     = (predecessor router, link used to reach v from predecessor)
    dist: Dict[RouterId, float] = {source: 0.0}
    prev: Dict[RouterId, Optional[tuple]] = {source: None}

    # heap: (cost, router_id)
    heap: list[tuple[float, Any]] = [(0.0, source)]

    visited: set[RouterId] = set()

    while heap:
        cost, u = heapq.heappop(heap)

        if u in visited:
            continue
        visited.add(u)

        for v in graph.neighbors(u):
            edge_cost = _edge_weight(graph, u, v)
            link_id   = _edge_link_id(graph, u, v)
            new_cost  = cost + edge_cost

            if new_cost < dist.get(v, INF):
                dist[v] = new_cost
                prev[v] = (u, link_id)
                heapq.heappush(heap, (new_cost, v))

    # Build routing table: for each destination, trace back to find
    # the *first* hop out of source.
    rt = RoutingTable(owner_id=source)

    for dst in dist:
        if dst == source:
            continue
        if dist[dst] == INF:
            continue  # unreachable — no entry added

        # Walk the predecessor chain back to source
        node = dst
        first_hop_router: RouterId = dst
        first_hop_link: LinkId = None  # type: ignore[assignment]

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
    """
    Compute routing tables for every router in the graph.

    Parameters
    ----------
    graph : networkx.Graph

    Returns
    -------
    dict[RouterId, RoutingTable]
        One fully-populated RoutingTable per node.

    Examples
    --------
    >>> import networkx as nx
    >>> G = nx.Graph()
    >>> G.add_edge("R1", "R2", weight=1, link_id="L12")
    >>> G.add_edge("R2", "R3", weight=1, link_id="L23")
    >>> tables = compute_all_routing_tables(G)
    >>> tables["R1"].lookup("R3")
    ('R2', 'L12')
    """
    tables: Dict[RouterId, RoutingTable] = {}
    for node in graph.nodes:
        tables[node] = dijkstra_single_source(graph, source=node)
    return tables
