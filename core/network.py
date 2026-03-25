# filename: core/network.py


"""
The File Define the Network Class
Network Class hold the informationa bout all router and links. and gives router a pre computed routes
"""

import logging
# use for creating and managing graphs
import networkx as nx
import simpy

from core.link import Link
from core.router import Router
from core.packet import Packet
from queueing.base import QueueDiscipline
from routing.routing_table import RoutingTable
from metrics.collector import MetricsCollector

log = logging.getLogger(__name__)

# Holds up all the router and links and find the paths between them
class Network:
    
    # Constructor
    def __init__(
        self,
        env: simpy.Environment,
        collector:MetricsCollector,
        queue_factory, # called function which return queue
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
    def add_router(self,router_id:str):
        self.graph.add_node(router_id)
        log.debug("Added router %s", router_id)
        
    # add link bewteen two router 
    def add_link(
        self,
        source_router_id:str,
        destination_router_id:str,
        bandwidth:float = 1_000_000,
        delay: float = 0.02,
        bidirectional:bool = True,
    ):
        for router_id in (source_router_id,destination_router_id):
            if router_id not in self.graph:
                self.add_router(router_id)
                
        self.add_directional_link(source_router_id,destination_router_id,bandwidth,delay)
        if bidirectional:
            self.add_directional_link(destination_router_id,source_router_id,bandwidth,delay)
        
    # add a edge to graph construct
    def add_directional_link(
        self,
        source:str,
        destination:str,
        bandwidth:float,
        delay:float,
    ):
        link = Link(self.env,source,destination,bandwidth,delay)
        self.links[(source,destination)] = link
        self.graph.add_edge(source,destination,weight=link.cost,link=link)
        
    
    # build the router and compute the routuing table using the given algorithm
    def build(self):
        
        # todo from om side, give the actual content from routing algorithm
        routing_tables  = self.routing_algorithm(self.graph,self.links)
        
        # todo after getting routing tables create router fror each and build a network
        
    