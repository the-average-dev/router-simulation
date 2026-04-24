# metrics/collector.py
"""
This File Defines the MetricsCollector Class
MetricsCollector Passively Listens to Events Fired by router.py
and Records them for Later Analysis by per_router.py and end_to_end.py

Contract File — Harshal's router.py calls these methods directly.
"""

import logging

logger = logging.getLogger(__name__)

# Event Record — One Entry Per Router Event


class PacketEvent:
    # Constructor
    def __init__(
        self,
        router_id: str,  # ID of the router where event occurred e.g. 'R1'
        packet_id: int,  # ID of the packet involved
        traffic_type: str,  # 'voip' | 'bulk' | 'best_effort'
        time: float,  # SimPy simulation time when event fired
        extra: dict = {},  # Optional extra data e.g. next_hop, delay
    ):
        self.router_id = router_id
        self.packet_id = packet_id
        self.traffic_type = traffic_type
        self.time = time
        self.extra = extra if extra is not None else {}

    # Representation of a PacketEvent
    def __repr__(self) -> str:
        return (
            f"PacketEvent(router={self.router_id}, pkt={self.packet_id}, "
            f"type={self.traffic_type}, t={self.time:.4f})"
        )


# MetricsCollector — Passive Event Listener


class MetricsCollector:
    # Constructor — initializes one list per event type
    def __init__(self):
        self.arrivals: list[PacketEvent] = []  # every packet that reaches a router
        self.enqueues: list[PacketEvent] = []  # every packet successfully queued
        self.drops: list[PacketEvent] = []  # every packet dropped (queue full)
        self.forwards: list[PacketEvent] = []  # every packet sent to next hop
        self.deliveries: list[PacketEvent] = []  # every packet that reached destination

    # Contract Methods

    # Called when a packet arrives at a router — before queueing decision
    def on_arrival(self, router_id: str, packet, time: float) -> None:
        self.arrivals.append(
            PacketEvent(
                router_id=router_id,
                packet_id=packet.id,
                traffic_type=packet.traffic_type,
                time=time,
            )
        )
        logger.debug("ARRIVAL  pkt=%s router=%s t=%.4f", packet.id, router_id, time)

    # Called when a packet is successfully added to the queue
    def on_enqueue(self, router_id: str, packet, time: float) -> None:
        self.enqueues.append(
            PacketEvent(
                router_id=router_id,
                packet_id=packet.id,
                traffic_type=packet.traffic_type,
                time=time,
            )
        )
        logger.debug("ENQUEUE  pkt=%s router=%s t=%.4f", packet.id, router_id, time)

    # Called when a packet is dropped because the queue is full
    def on_drop(self, router_id: str, packet, time: float) -> None:
        self.drops.append(
            PacketEvent(
                router_id=router_id,
                packet_id=packet.id,
                traffic_type=packet.traffic_type,
                time=time,
            )
        )
        logger.debug("DROP     pkt=%s router=%s t=%.4f", packet.id, router_id, time)

    # Called when a packet is forwarded to the next hop router
    def on_forward(self, router_id: str, packet, next_hop: str, time: float) -> None:
        self.forwards.append(
            PacketEvent(
                router_id=router_id,
                packet_id=packet.id,
                traffic_type=packet.traffic_type,
                time=time,
                extra={"next_hop": next_hop},  # store where it was sent
            )
        )
        logger.debug(
            "FORWARD  pkt=%s router=%s -> %s t=%.4f",
            packet.id,
            router_id,
            next_hop,
            time,
        )

    # Called when a packet reaches its final destination router
    # Delay is computed here: current time minus when packet was born
    def on_deliver(self, packet, time: float) -> None:
        delay = time - packet.arrival_time
        self.deliveries.append(
            PacketEvent(
                router_id="DEST",
                packet_id=packet.id,
                traffic_type=packet.traffic_type,
                time=time,
                extra={
                    "arrival_time": packet.arrival_time,  # birth time of the packet
                    "delay": delay,  # end-to-end delay in seconds
                },
            )
        )
        logger.debug("DELIVER  pkt=%s delay=%.4f", packet.id, delay)

    # Helper Method
    # Returns a quick count of all recorded events
    # Can call this while testing router.py to confirm hooks fire
    def summary(self) -> dict:
        return {
            "total_arrivals": len(self.arrivals),
            "total_enqueued": len(self.enqueues),
            "total_dropped": len(self.drops),
            "total_forwarded": len(self.forwards),
            "total_delivered": len(self.deliveries),
        }
