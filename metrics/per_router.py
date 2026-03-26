# metrics/per_router.py
"""
This File Defines the PerRouterMetrics Class
PerRouterMetrics Reads Data from MetricsCollector and Computes
Per-Router Statistics:
    - Drop Rate        : drops / arrivals per router
    - Utilization %    : enqueued / arrivals per router
    - Queue Length     : number of packets in queue at each timestamp
"""

import logging
from metrics.collector import MetricsCollector, PacketEvent

logger = logging.getLogger(__name__)


# RouterStats — Holds Computed Stats for One Router

class RouterStats:

    # Constructor
    def __init__(self, router_id: str):
        self.router_id        = router_id       # e.g. 'R1'
        self.total_arrivals   = 0               # total packets that arrived
        self.total_enqueued   = 0               # total packets successfully queued
        self.total_dropped    = 0               # total packets dropped
        self.drop_rate        = 0.0             # drops / arrivals (0.0 to 1.0)
        self.utilization      = 0.0             # enqueued / arrivals (0.0 to 1.0)
        self.queue_length_over_time: list[tuple[float, int]] = []
        # list of (timestamp, queue_length) — one entry per enqueue or drop event

    # Representation of RouterStats
    def __repr__(self) -> str:
        return (
            f"RouterStats(router={self.router_id}, "
            f"arrivals={self.total_arrivals}, "
            f"dropped={self.total_dropped}, "
            f"drop_rate={self.drop_rate:.2%}, "
            f"utilization={self.utilization:.2%})"
        )

# PerRouterMetrics — Computes Stats Per Router

class PerRouterMetrics:

    # Constructor — takes the shared collector from simulation.py
    def __init__(self, collector: MetricsCollector):
        self.collector = collector

    # Internal Helpers

    # Groups a flat list of PacketEvents by router_id
    # Returns { 'R1': [event, event, ...], 'R2': [...] }
    def _group_by_router(self, events: list[PacketEvent]) -> dict[str, list[PacketEvent]]:
        grouped: dict[str, list[PacketEvent]] = {}
        for event in events:
            if event.router_id not in grouped:
                grouped[event.router_id] = []
            grouped[event.router_id].append(event)
        return grouped

    # Computes queue length at each point in time for one router
    # Each enqueue adds 1, each drop or forward subtracts 1
    # Returns list of (timestamp, queue_length) tuples
    def _compute_queue_length(self, router_id: str) -> list[tuple[float, int]]:

        # collect all relevant events for this router and sort by time
        events: list[tuple[float, str]] = []

        for e in self.collector.enqueues:
            if e.router_id == router_id:
                events.append((e.time, "enqueue"))

        for e in self.collector.forwards:
            if e.router_id == router_id:
                events.append((e.time, "forward"))

        for e in self.collector.drops:
            if e.router_id == router_id:
                events.append((e.time, "drop"))

        # sort all events by timestamp
        events.sort(key=lambda x: x[0])

        # walk through events and track running queue length
        queue_length = 0
        timeline: list[tuple[float, int]] = []

        for time, event_type in events:
            if event_type == "enqueue":
                queue_length += 1           # packet entered the queue
            elif event_type in ("forward", "drop"):
                queue_length -= 1           # packet left the queue
                if queue_length < 0:
                    queue_length = 0        # safety clamp — should not go negative
            timeline.append((time, queue_length))

        return timeline

    # Main Compute Method

    # Computes stats for ALL routers seen in the collector
    # Returns { 'R1': RouterStats, 'R2': RouterStats, ... }
    def compute(self) -> dict[str, RouterStats]:

        # group each event type by router
        arrivals_by_router = self._group_by_router(self.collector.arrivals)
        enqueues_by_router = self._group_by_router(self.collector.enqueues)
        drops_by_router    = self._group_by_router(self.collector.drops)

        # get all unique router ids seen across all event types
        all_router_ids = set(arrivals_by_router) | set(enqueues_by_router) | set(drops_by_router)

        results: dict[str, RouterStats] = {}

        for router_id in all_router_ids:

            stats = RouterStats(router_id)

            # count raw totals
            stats.total_arrivals = len(arrivals_by_router.get(router_id, []))
            stats.total_enqueued = len(enqueues_by_router.get(router_id, []))
            stats.total_dropped  = len(drops_by_router.get(router_id, []))

            # compute drop rate — avoid divide by zero
            if stats.total_arrivals > 0:
                stats.drop_rate   = stats.total_dropped  / stats.total_arrivals
                stats.utilization = stats.total_enqueued / stats.total_arrivals
            else:
                stats.drop_rate   = 0.0
                stats.utilization = 0.0

            # compute queue length timeline for this router
            stats.queue_length_over_time = self._compute_queue_length(router_id)

            logger.debug("STATS %s", stats)
            results[router_id] = stats

        return results

    # Helper: Print a Quick Summary Table

    # Prints a formatted table of all router stats to stdout
    # Useful during experiments to get a quick overview
    def print_summary(self) -> None:
        stats = self.compute()
        print(f"\n{'Router':<10} {'Arrivals':<12} {'Enqueued':<12} {'Dropped':<10} {'Drop Rate':<12} {'Utilization'}")
        print("-" * 65)
        for router_id, s in sorted(stats.items()):
            print(
                f"{s.router_id:<10} {s.total_arrivals:<12} {s.total_enqueued:<12} "
                f"{s.total_dropped:<10} {s.drop_rate:<12.2%} {s.utilization:.2%}"
            )