"""
routing/bellman_ford.py
=======================
Distance-vector routing via the Bellman-Ford algorithm.

Why Bellman-Ford instead of Dijkstra here?
------------------------------------------
Bellman-Ford handles *dynamic* topologies: when a link fails mid-simulation,
router.py (or link_failure.py) can call ``recompute()`` on a BellmanFordRouter
and get updated tables in O(R * E) time without restarting the sim.
It also handles negative-weight edges (not expected in practice, but correct).

Input
-----
A networkx graph with the same edge-attribute contract as dijkstra.py:
    * 'weight'  (float, default 1) — link cost
    * 'link_id' (any, default (u,v)) — SimPy link identifier

Output
------
    {router_id: RoutingTable}

Algorithm
---------
Classic Bellman-Ford: relax all edges (R-1) times.
Negative-cycle detection is included (raises ValueError).

Usage pattern for link-failure events
--------------------------------------
    router = BellmanFordRouter(graph)
    tables = router.compute()

    # … link L23 fails …
    graph.remove_edge("R2", "R3")
    tables = router.recompute()   # re-runs on updated graph

No SimPy. No core/ imports.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import networkx as nx

from routing.routing_table import RoutingTable, RouterId, LinkId

INF = float("inf")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _edge_weight(graph: nx.Graph, u: RouterId, v: RouterId) -> float:
    return graph[u][v].get("weight", 1)


def _edge_link_id(graph: nx.Graph, u: RouterId, v: RouterId) -> LinkId:
    return graph[u][v].get("link_id", (u, v))


# ---------------------------------------------------------------------------
# Single-source Bellman-Ford
# ---------------------------------------------------------------------------

def bellman_ford_single_source(
    graph: nx.Graph,
    source: RouterId,
) -> RoutingTable:
    """
    Run Bellman-Ford from *source* and return its RoutingTable.

    Parameters
    ----------
    graph  : networkx.Graph (undirected) or DiGraph.
    source : router id.

    Returns
    -------
    RoutingTable for *source*.

    Raises
    ------
    ValueError
        If a negative-weight cycle is detected.
    """
    nodes: List[RouterId] = list(graph.nodes)
    n = len(nodes)

    dist: Dict[RouterId, float] = {v: INF for v in nodes}
    dist[source] = 0.0

    # prev[v] = (predecessor, link_id) on the shortest path to v
    prev: Dict[RouterId, Optional[Tuple[RouterId, LinkId]]] = {v: None for v in nodes}

    # Build edge list (for undirected graphs each edge appears once;
    # we add both directions so Bellman-Ford works correctly)
    edges: List[Tuple[RouterId, RouterId, float, LinkId]] = []
    for u, v in graph.edges():
        w    = _edge_weight(graph, u, v)
        lid  = _edge_link_id(graph, u, v)
        edges.append((u, v, w, lid))
        if not graph.is_directed():
            edges.append((v, u, w, lid))

    # Relax |V| - 1 times
    for _ in range(n - 1):
        updated = False
        for u, v, w, lid in edges:
            if dist[u] != INF and dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                prev[v] = (u, lid)
                updated = True
        if not updated:
            break   # early exit: converged

    # Negative-cycle check (one more pass)
    for u, v, w, _lid in edges:
        if dist[u] != INF and dist[u] + w < dist[v]:
            raise ValueError(
                f"Negative-weight cycle detected in graph (affects {u} → {v})."
            )

    # Build RoutingTable — trace back to find first hop from source
    rt = RoutingTable(owner_id=source)

    for dst in nodes:
        if dst == source:
            continue
        if dist[dst] == INF:
            continue  # unreachable

        # Trace predecessor chain back to source
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


# ---------------------------------------------------------------------------
# Convenience: compute tables for all routers
# ---------------------------------------------------------------------------

def compute_all_routing_tables(
    graph: nx.Graph,
) -> Dict[RouterId, RoutingTable]:
    """
    Run Bellman-Ford from every node and return all routing tables.

    Examples
    --------
    >>> import networkx as nx
    >>> G = nx.Graph()
    >>> G.add_edge("R1", "R2", weight=1, link_id="L12")
    >>> G.add_edge("R2", "R3", weight=2, link_id="L23")
    >>> tables = compute_all_routing_tables(G)
    >>> tables["R1"].lookup("R3")
    ('R2', 'L12')
    """
    return {node: bellman_ford_single_source(graph, source=node) for node in graph.nodes}


# ---------------------------------------------------------------------------
# Stateful wrapper for re-computation on topology changes
# ---------------------------------------------------------------------------

class BellmanFordRouter:
    """
    Stateful wrapper around Bellman-Ford that supports incremental re-computation
    when the network topology changes (link failure / recovery).

    Parameters
    ----------
    graph : nx.Graph
        The live topology graph.  Mutate this externally (add/remove edges)
        then call ``recompute()`` to refresh the routing tables.

    Examples
    --------
    >>> router = BellmanFordRouter(graph)
    >>> tables = router.compute()          # initial run

    >>> graph.remove_edge("R2", "R3")     # simulate link failure
    >>> tables = router.recompute()        # re-runs BF on updated graph
    """

    def __init__(self, graph: nx.Graph) -> None:
        self._graph = graph
        self._tables: Dict[RouterId, RoutingTable] = {}

    def compute(self) -> Dict[RouterId, RoutingTable]:
        """Run Bellman-Ford on the current graph. Stores and returns tables."""
        self._tables = compute_all_routing_tables(self._graph)
        return self._tables

    def recompute(self) -> Dict[RouterId, RoutingTable]:
        """Alias for compute() — semantically signals a topology-triggered rerun."""
        return self.compute()

    def get_table(self, router_id: RouterId) -> Optional[RoutingTable]:
        """Return the cached RoutingTable for *router_id*, or None if not computed yet."""
        return self._tables.get(router_id)

    @property
    def tables(self) -> Dict[RouterId, RoutingTable]:
        return self._tables
