# filename: main.py

"""
The Main Python File.
Entry Point for CLI for router simulation
"""

import json
import logging
import sys

from core.simulation import Simulation
from metrics.collector import MetricsCollector
from metrics.end_to_end import EndToEndMetrics
from metrics.per_router import PerRouterMetrics


def run_simulation(config: dict) -> None:

    discipline = config.get("queueing", {}).get("discipline", "fifo")
    queue_cap = config.get("queueing", {}).get("queue_cap", 50)
    algorithm = config.get("routing", {}).get("algorithm", "dijkstra")
    topology = config.get("network", {}).get("topology", "linear")

    # Queue factory
    if discipline == "fifo":
        from queueing.fifo import FifoQueue

        queue_factory = lambda: FifoQueue(capacity=queue_cap)
    elif discipline == "priority":
        from queueing.priority_queue import PriorityQueue

        queue_factory = lambda: PriorityQueue(capacity=queue_cap)
    elif discipline == "wfq":
        from queueing.wfq import WFQQueue

        custom_weights = config.get("queueing", {}).get("wfq_weights")
        if custom_weights:
            custom_weights = {int(k): float(v) for k, v in custom_weights.items()}

        queue_factory = lambda: WFQQueue(capacity=queue_cap, weights=custom_weights)
    elif discipline == "red":
        from queueing.red import REDQueue

        # Grab parameters from config, with safe defaults
        queue_cfg = config.get("queueing", {})
        p_max = queue_cfg.get("red_p_max", 0.10)
        wq = queue_cfg.get("red_wq", 0.002)
        sim_seed = config.get("simulation", {}).get("random_seed", 42)

        # Dynamically scale thresholds to prevent ValueError
        queue_factory = lambda: REDQueue(
            capacity=queue_cap,
            t_min=queue_cap * 0.3,
            t_max=queue_cap * 0.8,
            p_max=p_max,
            wq=wq,
            seed=sim_seed,
        )

    # Routing algorithm
    if algorithm == "dijkstra":
        from routing.dijkstra import compute_all_routing_tables

        routing_algorithm = compute_all_routing_tables
    elif algorithm == "bellman_ford":
        from routing.bellman_ford import compute_all_routing_tables

        routing_algorithm = compute_all_routing_tables
    else:
        raise ValueError(f"Unknown routing algorithm: '{algorithm}'")

    # Topology factory
    if topology == "linear":
        from topology.linear import LinearTopology

        topology_factory = LinearTopology()
    elif topology == "mesh":
        from topology.mesh import MeshTopology

        topology_factory = MeshTopology()
    elif topology == "star":
        from topology.star import StarTopology

        topology_factory = StarTopology()
    elif topology == "ring":
        from topology.ring import RingTopology

        topology_factory = RingTopology()
    elif topology == "tree":
        from topology.tree import TreeTopology

        topology_factory = TreeTopology()
    elif topology == "partial_mesh":
        from topology.partial_mesh import PartialMeshTopology

        topology_factory = PartialMeshTopology()
    else:
        raise ValueError(f"Unknown topology: '{topology}'")

    # Traffic generator
    from traffic.generator import generator as traffic_generator

    collector = MetricsCollector()

    sim = Simulation(
        config=config,
        topology_factory=topology_factory,
        queue_factory=queue_factory,
        routing_algorithm=routing_algorithm,
        traffic_generator=traffic_generator,
        collector=collector,
    )
    sim.run()

    # Print text results
    PerRouterMetrics(collector).print_summary()
    EndToEndMetrics(collector).print_summary()

    # Generate and save the graphs!
    try:
        from viz.plot_delay_cdf import DelayCDFPlotter
        from viz.plot_metrics import MetricsPlotter
        from viz.plot_topology import TopologyPlotter

        print("\nGenerating visual graphs... Saving to 'graphs/' folder.")

        # Pass collector to plotters. They will auto-create the "graphs" folder
        plotter = MetricsPlotter(collector, out_dir="graphs")
        plotter.plot_queue_length()
        plotter.plot_drop_and_utilization()

        cdf_plotter = DelayCDFPlotter(collector, out_dir="graphs")
        cdf_plotter.plot_cdf(split_by_type=True)

        print("Graphs successfully generated in the 'graphs/' directory.")

    except ImportError as e:
        print(f"\n[Warning] Could not load visualization modules: {e}")
        print("Please ensure 'matplotlib' is installed.")


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    config_path = ""

    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        print("No configuration file provided.")
        config_path = input("Please enter the path to your config file: ").strip()

    if not config_path:
        print("Error: No config path provided. Exiting.")
        return

    try:
        with open(config_path, "r") as f:
            config_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find file '{config_path}'")
        return
    except json.JSONDecodeError:
        print(f"Error: '{config_path}' is not a valid JSON file.")
        return

    run_simulation(config_data)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[Simulation Aborted] Exiting gracefully...")
        sys.exit(0)
