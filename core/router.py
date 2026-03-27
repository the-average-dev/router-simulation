# filename: core/router.py


"""
This File Define the Router Class
Router Class handles the working of router and its full lifecycle
"""

import logging
import simpy

from core.packet import Packet
from routing.routing_table import RoutingTable
from queueing.base import QueueDiscipline
from metrics.collector import MetricsCollector

log = logging.getLogger(__name__)


class Router:


    # Constructor
    def __init__(
        self,
        env: simpy.Environment,
        router_id: str,
        queue: QueueDiscipline,
        routing_table: RoutingTable,
        collector:MetricsCollector
    ) -> None:
        self.env = env
        self.id = router_id
        self.queue = queue
        self.routing_table = routing_table
        self.collector = collector
        self.packet_ready = env.event()
        self.deliver_to = None
        
        # Start the forwarding process
        env.process(self.forwarding_loop())



    # get the packet from queue one by one and forward them
    def forwarding_loop(self):
        
        while True:
            
            if self.queue.length() == 0:
                self.packet_ready = self.env.event()
                yield self.packet_ready
                
            packet = self.queue.dequeue()
            if packet is None:
                continue
            
            # get the entry from next hop from routing table
            route = self.routing_table.next_hop(packet.dst)
            
            if route is None:
                log.warning(
                    "%.4f  %s has no route to %s — dropping %s",
                    self.env.now, 
                    self.id, 
                    packet.dst, 
                    packet
                )
                
                self.collector.on_drop(self.id,packet,self.env.now)
                continue
            
            # get the next router id and link
            next_hop_id,link = route
            log.debug(
                "%.4f  %s forwarding %s → %s via %s",
                self.env.now, 
                self.id, 
                packet, 
                next_hop_id, 
                link,
            )
            
            self.collector.on_forward(self.id,packet,next_hop_id,self.env.now)
            # wait for it to transmit
            yield from link.transmit(packet)
            
            # hand the packet to next router, will get the next router via callback
            if self.deliver_to is not None:
                next_router = self.deliver_to(next_hop_id)
                if next_router is not None:
                    next_router.receive(packet)
            
    # will called by network
    def set_delivery_callback(self, callback):    
        self.deliver_to = callback    

    # called when packet arrives at this router interface
    def receive(self, packet: Packet):
        log.debug("%.4f  %s received %s", self.env.now, self.id, packet)
        self.collector.on_arrival(self.id, packet, self.env.now)
        
        if packet.dst == self.id:
            log.debug("%.4f  %s DELIVERED %s", self.env.now, self.id, packet)
            self.collector.on_deliver(packet, self.env.now)
            return
        
        accepted = self.queue.enqueue(packet)
        
        if accepted:
            self.collector.on_enqueue(self.id,packet,self.env.now)
            
            if not self.packet_ready.triggered:
                self.packet_ready.succeed()
        else:
            log.debug("%.4f  %s DROPPED %s (queue full)", self.env.now, self.id, packet)
            self.collector.on_drop(self.id, packet, self.env.now)
            

    # Represenation of the Router
    def __repr__(self) -> str:
        return f"Router({self.id}, queue_len={self.queue.length()})"