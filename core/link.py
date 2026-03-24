# filename: core/link.py

"""
The File Define the Link Class
Link Class is the physical connection between two routers
"""

# imports
import logging
import simpy

# Setting up logging for this module
log = logging.getLogger(__name__)

class Link:

    # Constructor
    def __init__(
        self,
        env: simpy.Environment,
        source_router: str,
        destination_router: str,
        bandwidth: float = 1_000_000, # bits per second
        propagation_delay: float = 0.002,         # propagation delay in seconds
    ):
        self.env = env
        self.src_id = source_router
        self.dst_id = destination_router
        self.bandwidth = bandwidth
        self.delay = propagation_delay
        self.resource = simpy.Resource(env, capacity=1)
        self.is_up = True

    # calculate the delay and simulate the transmission of a packet from one router to another
    def transmit(self, packet):
        
        if not self.is_up:
            log.warning(f"Link {self.src_id}->{self.dst_id} DOWN. Packet {packet.id} dropped.")
            return

        tx_delay = (packet.size * 8) / self.bandwidth
        total_delay = tx_delay + self.delay

        with self.resource.request() as req:
            yield req  # Wait until the link is free
            yield self.env.timeout(total_delay) # Simulate travel time

    # Representation of the Packet Transmission
    def __repr__(self) -> str:
        return f"Link({self.src_id}->{self.dst_id}, {self.bandwidth}bps)"
        
    # Cost of using this router
    def cost(self) -> float:
        return 1.0 / self.bandwidth