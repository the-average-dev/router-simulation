# filename: core/router.py


"""
This File Define the Router Class
Router Class handles the working of router and its full lifecycle
"""

import logging
import simpy

from core.packet import Packet
from routing.routing_table import RoutingTable

log = logging.getLogger(__name__)


class Router:


    # Constructor
    def __init__(
        self,
        env: simpy.Environment,
        router_id: str,
        queue, # TODO: Queueing File Logic import from OM
        routing_table: RoutingTable,
        collector # TODO: Metrics File Logic import from Sidd
    ) -> None:
        self.env = env
        self.id = router_id
        self.queue = queue
        self.routing_table = routing_table
        self.collector = collector
        self.packet_ready = env.event()
        
        # Start the forwarding process
        env.process(self.forwarding_loop())



    # get the packet from queue one by one and forward them
    def forwarding_loop(self):
        # TODO: forwarding logic when queue code is avaiable
        pass

    # Represenation of the Router
    def __repr__(self) -> str:
        return f"Router({self.id}, queue_len={self.queue.length()})"