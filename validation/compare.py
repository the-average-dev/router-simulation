# validation/compare.py
"""
This File Defines the SimComparator Class
SimComparator Takes Two Values Measured from the Simulation
and Compares them Against M/M/1 Analytical Values
A Difference Under 5% on Both Metrics Means the Simulation is Correct
"""

import logging
from validation.mm1 import MM1Queue

logger = logging.getLogger(__name__)


# Compares Simulation Results Against M/M/1 Analytical Values
class SimComparator:

    # Constructor
    # arrival_rate and service_rate must match what was used in the sim
    def __init__(
        self,
        arrival_rate: float,
        service_rate: float,
    ):
        self.arrival_rate = arrival_rate
        self.service_rate = service_rate
        self.mm1 = MM1Queue(arrival_rate, service_rate)

    # Computes percentage difference between sim value and theory value
    def _delta(self, sim_value: float, theory_value: float) -> float:
        if theory_value == 0:
            return 0.0
        return abs(sim_value - theory_value) / theory_value * 100

    # Prints a comparison table of sim vs theory
    # sim_avg_queue_len — average queue length measured from your sim
    # sim_avg_delay     — average packet delay measured from your sim
    def print_report(
        self,
        sim_avg_queue_len: float,
        sim_avg_delay: float,
    ) -> None:

        # get analytical values
        theory = self.mm1.compute()

        # compute percentage difference for each metric
        delta_queue = self._delta(sim_avg_queue_len, theory.exp_queue_len)
        delta_delay = self._delta(sim_avg_delay, theory.exp_delay)

        # pass if under 5%
        queue_status = "PASS" if delta_queue < 5.0 else "FAIL"
        delay_status = "PASS" if delta_delay < 5.0 else "FAIL"
        overall = "PASS" if queue_status == "PASS" and delay_status == "PASS" else "FAIL"

        logger.debug(
            "delta queue=%.2f%% delay=%.2f%%",
            delta_queue, delta_delay
        )

        # print the report
        print(f"\nValidation Report")
        print(f"Arrival Rate : {self.arrival_rate:.4f} packets/sec")
        print(f"Service Rate : {self.service_rate:.4f} packets/sec")
        print(f"Utilization : {theory.rho:.4f}")
        print()
        print(f"{'Metric':<20} {'Sim':>10} {'Theory':>10} {'Delta':>10} {'Status':>8}")
        print("-" * 62)
        print(
            f"{'Avg Queue Length':<20} {sim_avg_queue_len:>10.4f} "
            f"{theory.exp_queue_len:>10.4f} "
            f"{delta_queue:>9.2f}% {queue_status:>8}"
        )
        print(
            f"{'Avg Delay (sec)':<20} {sim_avg_delay:>10.4f} "
            f"{theory.exp_delay:>10.4f} "
            f"{delta_delay:>9.2f}% {delay_status:>8}"
        )
        print("-" * 62)
        print(f"Overall: {overall}")