# metrics/end_to_end.py
"""
This File Defines the EndToEndMetrics Class
EndToEndMetrics Reads Data from MetricsCollector and Computes
End to End Statistics Across the Entire Network:
    - Average Delay      : average time a packet took from source to destination
    - Throughput         : how many packets were delivered per second
    - Average Hop Count  : average number of routers a packet passed through
"""

import logging
from metrics.collector import MetricsCollector

logger = logging.getLogger(__name__)


# Holds the Computed End to End Results
class EndToEndResult:

    # Constructor
    def __init__(
        self,
        avg_delay:     float,   # average delay across all delivered packets in seconds
        throughput:    float,   # delivered packets per second
        avg_hop_count: float,   # average number of routers a packet passed through
        total_delivered: int,   # total number of packets that reached destination
        total_dropped:   int,   # total number of packets dropped across all routers
    ):
        self.avg_delay      = avg_delay
        self.throughput     = throughput
        self.avg_hop_count  = avg_hop_count
        self.total_delivered = total_delivered
        self.total_dropped   = total_dropped

    # Representation of EndToEndResult
    def __repr__(self) -> str:
        return (
            f"EndToEndResult("
            f"avg_delay={self.avg_delay:.4f}s, "
            f"throughput={self.throughput:.4f} pkts/sec, "
            f"avg_hops={self.avg_hop_count:.2f}, "
            f"delivered={self.total_delivered}, "
            f"dropped={self.total_dropped})"
        )


# Computes End to End Metrics Across the Whole Network
class EndToEndMetrics:

    # Constructor — takes the shared collector from simulation.py
    def __init__(self, collector: MetricsCollector):
        self.collector = collector

    # Computes average delay across all delivered packets
    # Delay for one packet = delivery time - arrival_time (stored in extra)
    def _compute_avg_delay(self) -> float:
        deliveries = self.collector.deliveries

        # if no packets were delivered return 0
        if len(deliveries) == 0:
            return 0.0

        # sum up all delays stored in extra by on_deliver
        total_delay = 0.0
        for event in deliveries:
            total_delay += event.extra["delay"]

        return total_delay / len(deliveries)

    # Computes throughput — delivered packets per second
    # Throughput = total delivered / total simulation time
    # Total sim time = last delivery time - first arrival time
    def _compute_throughput(self) -> float:
        deliveries = self.collector.deliveries
        arrivals   = self.collector.arrivals

        # need at least one delivery and one arrival
        if len(deliveries) == 0 or len(arrivals) == 0:
            return 0.0

        # first arrival time across all routers
        first_arrival_time = min(event.time for event in arrivals)

        # last delivery time
        last_delivery_time = max(event.time for event in deliveries)

        # total simulation duration
        sim_duration = last_delivery_time - first_arrival_time

        # avoid division by zero if sim ran for no time
        if sim_duration <= 0:
            return 0.0

        return len(deliveries) / sim_duration

    # Computes average hop count per packet
    # Hop count for one packet = number of times it was forwarded
    def _compute_avg_hop_count(self) -> float:
        forwards = self.collector.forwards

        # if no packets were forwarded return 0
        if len(forwards) == 0:
            return 0.0

        # count how many times each packet was forwarded
        # key = packet_id, value = hop count
        hop_counts: dict[int, int] = {}
        for event in forwards:
            if event.packet_id not in hop_counts:
                hop_counts[event.packet_id] = 0
            hop_counts[event.packet_id] += 1

        # average hop count across all packets that were forwarded
        total_hops = sum(hop_counts.values())
        return total_hops / len(hop_counts)

    # Runs all computations and returns EndToEndResult
    def compute(self) -> EndToEndResult:

        avg_delay     = self._compute_avg_delay()
        throughput    = self._compute_throughput()
        avg_hop_count = self._compute_avg_hop_count()

        total_delivered = len(self.collector.deliveries)
        total_dropped   = len(self.collector.drops)

        result = EndToEndResult(
            avg_delay       = avg_delay,
            throughput      = throughput,
            avg_hop_count   = avg_hop_count,
            total_delivered = total_delivered,
            total_dropped   = total_dropped,
        )

        logger.debug("EndToEnd result: %s", result)
        return result

    # Prints a simple summary of end to end results
    def print_summary(self) -> None:
        result = self.compute()
        print(f"\nEnd to End Metrics")
        print(f"Total Delivered  : {result.total_delivered} packets")
        print(f"Total Dropped    : {result.total_dropped} packets")
        print(f"Avg Delay        : {result.avg_delay:.4f} seconds")
        print(f"Throughput       : {result.throughput:.4f} packets/sec")
        print(f"Avg Hop Count    : {result.avg_hop_count:.2f} hops")