# filename: routing/routing_table.py

"""
This File Defines the RoutingTable Class
Data structure: {destination_router_id: (next_hop_id, link_object)}
Each router holds one of these. next_hop(dst) returns (next_hop_id, link)
so router.py can unpack and call link.transmit().
"""


class RoutingTable:
    def __init__(self, router_id: str) -> None:
        self.router_id: str = router_id
        self._table: dict = {}

    # Called by network.py and routing algorithms to populate the table
    def add_route(self, destination: str, next_hop: str, link) -> None:
        self._table[destination] = (next_hop, link)

    # Called by router.py — returns (next_hop_id, link) tuple or None
    def next_hop(self, destination: str):
        return self._table.get(destination)

    def __repr__(self) -> str:
        return f"RoutingTable(owner={self.router_id!r}, entries={len(self._table)})"
