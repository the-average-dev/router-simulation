# filename: routing/routing_table.py

"""
This File Define the Routing Table Class
Routing Table Class define the lookup table for next hop
"""

from core.link import Link


class RoutingTable:
    # Constructor
    def __init__(self, router_id: str):
        self.router_id = router_id
        # destination router id -> (next_hop router id, link class object)
        self.table: dict[str, tuple[str, Link]] = {}

    # inset a table entry
    def add_route(self, destination_router: str, next_hop: str, link):
        self.table[destination_router] = (next_hop, link)

    # return the table entry if exist else None
    def next_hop(self, destination_router: str):
        return self.table.get(destination_router)

    # remove the table entry
    def remove_route(self, dst: str):
        self.table.pop(dst, None)

    # get all the entries
    def all_destinations(self):
        return list(self.table.keys())

    # Representation of The Routing Table
    def __repr__(self) -> str:
        routes = ", ".join(f"{dst}→{nh}" for dst, (nh, _) in self.table.items())
        return f"RoutingTable({self.router_id}: [{routes}])"
