# experiments/exp_mm1_baseline.py
"""
This File Runs the M/M/1 Baseline Experiment
Single Router, FIFO Queue, Poisson Arrivals
This is the Most Important Experiment — it Validates the Simulation
Against M/M/1 Analytical Formulas
"""

import logging
from core.simulation import Simulation
from metrics.collector import MetricsCollector
from metrics.end_to_end import EndToEndMetrics
from metrics.per_router import PerRouterMetrics
from topology.linear import LinearTopology
from queueing.fifo import FifoQueue
from traffic.generator import generator
from validation.compare import SimComparator
from validation.steady_state import SteadyStateDetector

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger(__name__)


# config for a single router sim — simplest possible setup
CONFIG = {
    "simulation": {
        "random_seed": 42,
        "duration": 500
    },
    "network": {
        "num_routers": 2,       # 2 routers — src and dst
        "link_bandwidth": 1000000,
        "link_delay": 0.002
    },
    "traffic": {
        "arrival_rate": 0.8,    # lambda — 0.8 packets per second
        "classes": ["voip", "bulk", "best_effort"],
        "class_weights": [0.2, 0.3, 0.5],
        "packet_size_mean": 512
    }
}

# service rate — how many packets the router handles per second
# must be greater than arrival_rate for a stable queue
SERVICE_RATE = 1.0


def run():

    print("\nRunning M/M/1 Baseline Experiment...")
    print(f"Arrival Rate  : {CONFIG['traffic']['arrival_rate']} packets/sec")
    print(f"Service Rate  : {SERVICE_RATE} packets/sec")
    print(f"Duration      : {CONFIG['simulation']['duration']} seconds")

    # create a fresh collector
    collector = MetricsCollector()

    # wire up the simulation
    sim = Simulation(
        config            = CONFIG,
        topology_factory  = LinearTopology(),
        queue_factory     = lambda: FifoQueue(),
        routing_algorithm = None,       # uses fallback dijkstra
        traffic_generator = generator,
        collector         = collector,
    )

    # run the sim — collector gets filled with events
    sim.run()

    # print raw collector summary
    print("\nRaw Collector Summary:")
    summary = collector.summary()
    for key, value in summary.items():
        print(f"  {key} : {value}")

    # trim warmup phase — discard first 20% of sim time
    detector = SteadyStateDetector(collector)
    detector.print_summary()

    # compute end to end metrics
    e2e    = EndToEndMetrics(collector)
    result = e2e.compute()
    e2e.print_summary()

    # compute per router metrics
    per_router = PerRouterMetrics(collector)
    per_router.print_summary()

    # compare against M/M/1 theory
    comparator = SimComparator(
        arrival_rate = CONFIG["traffic"]["arrival_rate"],
        service_rate = SERVICE_RATE,
    )
    comparator.print_report(
        sim_avg_queue_len = result.avg_queue_len,
        sim_avg_delay     = result.avg_delay,
    )


if __name__ == "__main__":
    run()