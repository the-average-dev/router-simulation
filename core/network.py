# filename: core/network.py


"""
The File Define the Network Class
Network Class hold the informationa bout all router and links. and gives router a pre computed routes
"""

import logging

# use for creating and managing graphs
import networkx as nx
import simpy
from networkx.exception import NetworkXNoPath

from core.link import Link
from core.packet import Packet
from core.router import Router
from metrics.collector import MetricsCollector

# from queueing.base import QueueDiscipline
from routing.routing_table import RoutingTable

log = logging.getLogger(__name__)


# Holds up all the router and links and find the paths between them
class Network:
    # Constructor
    def __init__(
        self,
        env: simpy.Environment,
        collector: MetricsCollector,
        queue_factory,  # called function which return queue
        routing_algorithm,
    ):
        self.env = env
        self.collector = collector
        self.queue_factory = queue_factory
        self.routing_algorithm = routing_algorithm

        self.graph: nx.DiGraph = nx.DiGraph()
        self.routers: dict[str, Router] = {}
        self.links: dict[tuple[str, str], Link] = {}

    # add router to graph
    def add_router(self, router_id: str):
        self.graph.add_node(router_id)
        log.debug("Added router %s", router_id)

    # add link bewteen two router
    def add_link(
        self,
        source_router_id: str,
        destination_router_id: str,
        bandwidth: float = 1_000_000,
        delay: float = 0.02,
        bidirectional: bool = True,
    ):
        for router_id in (source_router_id, destination_router_id):
            if router_id not in self.graph:
                self.add_router(router_id)

        self.add_directional_link(
            source_router_id, destination_router_id, bandwidth, delay
        )
        if bidirectional:
            self.add_directional_link(
                destination_router_id, source_router_id, bandwidth, delay
            )

    # add a edge to graph construct
    def add_directional_link(
        self,
        source: str,
        destination: str,
        bandwidth: float,
        delay: float,
    ):
        link = Link(self.env, source, destination, bandwidth, delay)
        self.links[(source, destination)] = link
        self.graph.add_edge(source, destination, weight=link.cost, link=link)

    # build the router and compute the routuing table using the given algorithm
    def build(self):

        # todo from om side, give the actual content from routing algorithm
        if self.routing_algorithm is not None:
            routing_tables = self.routing_algorithm(self.graph, self.links)
        else:
            # use fallback for now

            log.warning("No routing_algorithm provided — using internal nx fallback. ")

            routing_tables = self.fall_back_routing_algorithm()

        for router_id in self.graph.nodes:
            routing_table = routing_tables.get(router_id, RoutingTable(router_id))
            router = Router(
                self.env, router_id, self.queue_factory(), routing_table, self.collector
            )
            router.set_delivery_callback(self.resolve_router)
            self.routers[router_id] = router

            log.debug("Built router %s with table: %s", router_id, routing_table)

        log.info(
            "Network built: %d routers, %d directed links",
            len(self.routers),
            len(self.links),
        )

    # fallback algorithm in case the user specify routing algorithm is not specify
    # may get remove in future
    def fall_back_routing_algorithm(self) -> dict[str, RoutingTable]:

        tables: dict[str, RoutingTable] = {}

        for source in self.graph.nodes:
            router = RoutingTable(source)

            for destination in self.graph.nodes:
                if destination == source:
                    continue
                try:
                    path = nx.shortest_path(
                        self.graph, source, destination, weight="weight"
                    )
                    if len(path) >= 2:
                        next_hop = path[1]
                        link = self.links.get((source, next_hop))
                        if link:
                            router.add_route(destination, next_hop, link)
                except NetworkXNoPath:
                    log.debug("No path from %s to %s", source, destination)

            tables[source] = router

        return tables

    def resolve_router(self, router_id: str) -> Router | None:
        return self.routers.get(router_id)

    # to inject a packet at specify router
    def inject(self, packet: Packet, at_router: str):
        router = self.routers.get(at_router)
        if router is None:
            raise ValueError(f"Router '{at_router}' not found in network")

        router.receive(packet)

    def get_router(self, router_id: str) -> Router | None:
        return self.routers.get(router_id)

    def router_ids(self) -> list[str]:
        return list(self.routers.keys())

    # to simulate link failure
    def take_down_link(self, source_id: str, destination_id: str):
        link = self.links.get((source_id, destination_id))

        if link:
            link.is_up = False
            log.warning("Link %s→%s is now DOWN", source_id, destination_id)

    def bring_up_link(self, source_id: str, destination_id: str):
        link = self.links.get((source_id, destination_id))

        if link:
            link.is_up = True
            log.info("Link %s→%s is back UP", source_id, destination_id)
