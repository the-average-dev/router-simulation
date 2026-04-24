# filename: core/router.py


"""
This File Define the Router Class
Router Class handles the working of router and its full lifecycle
"""

import logging

import simpy

from core.packet import Packet
from metrics.collector import MetricsCollector
from queueing.base import QueueDiscipline
from routing.routing_table import RoutingTable

log = logging.getLogger(__name__)


class Router:
    # Constructor
    def __init__(
        self,
        env: simpy.Environment,
        router_id: str,
        queue: QueueDiscipline,
        routing_table: RoutingTable,
        collector: MetricsCollector,
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

            route = self.routing_table.next_hop(packet.dst)

            if route is None:
                log.warning(
                    "%.4f  %s has no route to %s — dropping %s",
                    self.env.now,
                    self.id,
                    packet.dst,
                    packet,
                )
                self.collector.on_drop(self.id, packet, self.env.now)
                continue

            next_hop_id, link = route
            log.debug(
                "%.4f  %s forwarding %s → %s via %s",
                self.env.now,
                self.id,
                packet,
                next_hop_id,
                link,
            )

            # wait for it to transmit, capture the success status
            success = yield from link.transmit(packet)

            if success:
                # ONLY record as forwarded if the link actually carried it
                self.collector.on_forward(self.id, packet, next_hop_id, self.env.now)

                # hand the packet to next router
                if self.deliver_to is not None:
                    next_router = self.deliver_to(next_hop_id)
                    if next_router is not None:
                        next_router.receive(packet)
            else:
                # The link was down! Tell the collector we dropped it.
                self.collector.on_drop(self.id, packet, self.env.now)

    # will called by network
    def set_delivery_callback(self, callback):
        self.deliver_to = callback

    # called when packet arrives at this router interface

    def receive(self, packet: Packet):
        log.debug("%.4f  %s received %s", self.env.now, self.id, packet)

        if packet.dst == self.id:
            log.debug("%.4f  %s DELIVERED %s", self.env.now, self.id, packet)
            self.collector.on_deliver(packet, self.env.now)
            return

        # MOVE THIS HERE: Only count as an arrival if it didn't get delivered
        self.collector.on_arrival(self.id, packet, self.env.now)

        accepted = self.queue.enqueue(packet)

        if accepted:
            self.collector.on_enqueue(self.id, packet, self.env.now)
            if not self.packet_ready.triggered:
                self.packet_ready.succeed()
        else:
            log.debug("%.4f  %s DROPPED %s (queue full)", self.env.now, self.id, packet)
            self.collector.on_drop(self.id, packet, self.env.now)

    # Represenation of the Router
    def __repr__(self) -> str:
        return f"Router({self.id}, queue_len={self.queue.length()})"
