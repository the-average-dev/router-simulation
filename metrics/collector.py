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
    def __init__(
        self,
        router_id: str,
        packet_id: int,
        traffic_type: str,
        time: float,
        extra: dict | None = None,  # Set default to None
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
        self.arrivals: list = []  # every packet that reaches a router
        self.enqueues: list = []  # every packet successfully queued
        self.drops: list = []  # every packet dropped (queue full)
        self.forwards: list = []  # every packet sent to next hop
        self.deliveries: list = []  # every packet that reached destination

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
                extra={"next_hop": next_hop},
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
                    "arrival_time": packet.arrival_time,
                    "delay": delay,
                },
            )
        )
        logger.debug("DELIVER  pkt=%s delay=%.4f", packet.id, delay)

    # Returns a quick count of all recorded events
    def summary(self) -> dict:
        return {
            "total_arrivals": len(self.arrivals),
            "total_enqueued": len(self.enqueues),
            "total_dropped": len(self.drops),
            "total_forwarded": len(self.forwards),
            "total_delivered": len(self.deliveries),
        }
