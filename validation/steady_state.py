# validation/steady_state.py
"""
This File Defines the SteadyStateDetector Class
SteadyStateDetector Removes the Warmup Phase from Simulation Data
The First 20% of Simulation Time is Discarded
Only the Remaining 80% is Used for Computing Averages

Why — When the Sim Starts the Network is Completely Empty
This is Unrealistic so Early Measurements are Skewed
Cutting the First 20% Gives us Stable Realistic Results
"""

import logging
from metrics.collector import MetricsCollector, PacketEvent

logger = logging.getLogger(__name__)

# cut off the first 20% of simulation time
WARMUP_FRACTION = 0.20


# Holds the Trimmed Event Lists After Warmup is Removed
class SteadyStateResult:

    # Constructor
    def __init__(
        self,
        warmup_cutoff_time: float,      # time where warmup ends
        arrivals: list,       # arrival events after warmup
        enqueues: list,       # enqueue events after warmup
        drops: list,       # drop events after warmup
        forwards: list,       # forward events after warmup
        deliveries:list,       # delivery events after warmup
    ):
        self.warmup_cutoff_time = warmup_cutoff_time
        self.arrivals = arrivals
        self.enqueues = enqueues
        self.drops = drops
        self.forwards = forwards
        self.deliveries = deliveries

    # Representation of SteadyStateResult
    def __repr__(self) -> str:
        return (
            f"SteadyStateResult("
            f"cutoff={self.warmup_cutoff_time:.2f}s, "
            f"arrivals={len(self.arrivals)}, "
            f"deliveries={len(self.deliveries)}, "
            f"drops={len(self.drops)})"
        )


# Removes Warmup Phase and Returns Only Steady State Events
class SteadyStateDetector:

    # Constructor — takes the shared collector from simulation.py
    def __init__(self, collector: MetricsCollector):
        self.collector = collector

    # Finds the time where warmup ends
    # Cutoff = first arrival time + 20% of total sim duration
    def _compute_cutoff(self) -> float:
        arrivals = self.collector.arrivals

        if len(arrivals) == 0:
            return 0.0

        first_time   = min(event.time for event in arrivals)
        last_time    = max(event.time for event in arrivals)
        sim_duration = last_time - first_time

        cutoff = first_time + WARMUP_FRACTION * sim_duration

        logger.debug(
            "Warmup cutoff: %.2fs (first=%.2f last=%.2f duration=%.2f)",
            cutoff, first_time, last_time, sim_duration
        )

        return cutoff

    # Keeps only events that happened after the cutoff time
    def _trim(self, events: list[PacketEvent], cutoff: float) -> list[PacketEvent]:
        return [event for event in events if event.time >= cutoff]

    # Trims all event lists and returns SteadyStateResult
    def compute(self) -> SteadyStateResult:

        cutoff = self._compute_cutoff()

        result = SteadyStateResult(
            warmup_cutoff_time = cutoff,
            arrivals = self._trim(self.collector.arrivals,   cutoff),
            enqueues = self._trim(self.collector.enqueues,   cutoff),
            drops = self._trim(self.collector.drops,      cutoff),
            forwards = self._trim(self.collector.forwards,   cutoff),
            deliveries = self._trim(self.collector.deliveries, cutoff),
        )

        logger.debug("SteadyState: %s", result)
        return result

    # Prints a simple summary showing how much data was trimmed
    def print_summary(self) -> None:
        result = self.compute()

        print(f"\nSteady State Detection")
        print(f"Warmup Cutoff   : {result.warmup_cutoff_time:.2f} seconds")
        print(f"Warmup Fraction : first {WARMUP_FRACTION:.0%} of sim discarded")
        print()
        print(f"{'Event':<15} {'Total':>10} {'After Warmup':>15} {'Discarded':>12}")
        print("-" * 55)
        print(f"{'Arrivals':<15} {len(self.collector.arrivals):>10} {len(result.arrivals):>15} {len(self.collector.arrivals)  - len(result.arrivals):>12}")
        print(f"{'Enqueues':<15} {len(self.collector.enqueues):>10} {len(result.enqueues):>15} {len(self.collector.enqueues)  - len(result.enqueues):>12}")
        print(f"{'Drops':<15} {len(self.collector.drops):>10}    {len(result.drops):>15} {len(self.collector.drops)     - len(result.drops):>12}")
        print(f"{'Forwards':<15} {len(self.collector.forwards):>10} {len(result.forwards):>15} {len(self.collector.forwards)  - len(result.forwards):>12}")
        print(f"{'Deliveries':<15} {len(self.collector.deliveries):>10} {len(result.deliveries):>15} {len(self.collector.deliveries)- len(result.deliveries):>12}")