# filename: core/simulation.py


"""
This File Define the Top Simulation Class
Simulation Class starts and handle the simulation
"""

import json
import logging
import random

import simpy

from core.network import Network
from metrics.collector import MetricsCollector

log = logging.getLogger(__name__)


class Simulation:
    # Constructor
    def __init__(
        self,
        config: dict,
        topology_factory,
        queue_factory,
        routing_algorithm,
        traffic_generator,
        collector: MetricsCollector | None = None,
    ):

        self.config = config
        self.topology_factory = topology_factory
        self.queue_factory = queue_factory
        self.routing_algorithm = routing_algorithm
        self.traffic_generator = traffic_generator
        self.collector = collector or MetricsCollector()

    def run(self) -> MetricsCollector:

        # get the parameter and config from json file
        if "simulation" not in self.config:
            raise KeyError("Missing 'simulation' section in config")

        sim_config = self.config["simulation"]

        if "random_seed" not in sim_config:
            raise KeyError("Missing 'random_seed' in simulation config")

        seed = sim_config["random_seed"]

        if "duration" not in sim_config:
            raise KeyError("Missing 'duration' in simulation config")

        duration = sim_config["duration"]

        if seed != None:
            random.seed(seed)

        log.info("Simulation seed=%s duration=%s", seed, duration)

        # Create environement
        env = simpy.Environment()

        network = Network(
            env=env,
            collector=self.collector,
            queue_factory=self.queue_factory,
            routing_algorithm=self.routing_algorithm,
        )

        self.topology_factory(network, self.config)
        network.build()

        try:
            from viz.plot_topology import TopologyPlotter
            seed = self.config["simulation"]["random_seed"]
            TopologyPlotter(network, out_dir="graphs",seed=seed).plot()
        except ImportError:
            pass

        env.process(self.traffic_generator(env, network, self.config))

        failure_cfg = self.config.get("events", {}).get("link_failure", {})
        if failure_cfg.get("enabled", False):

            def chaos_monkey(env, net, cfg):
                trigger_time = cfg.get("trigger_time", duration / 2)
                fail_duration = cfg.get("duration", 100)

                yield env.timeout(trigger_time)

                if len(net.links) > 0:
                    edge = random.choice(list(net.links.keys()))
                    src, dst = edge

                    log.warning(
                        f"*** CHAOS MONKEY: Destroying link {src} <-> {dst} at t={env.now} ***"
                    )
                    net.take_down_link(src, dst)
                    net.take_down_link(dst, src)

                    algo = self.config.get("routing", {}).get("algorithm")
                    if algo in ["bellman_ford", "dijkstra"]:
                        log.warning(
                            f"*** CHAOS MONKEY: Recalculating routes using {algo}... ***"
                        )
                        new_tables = self.routing_algorithm(net.graph, net.links)
                        for r_id, r_obj in net.routers.items():
                            r_obj.routing_table = new_tables.get(
                                r_id, r_obj.routing_table
                            )

                    yield env.timeout(fail_duration)

                    log.warning(
                        f"*** CHAOS MONKEY: Repairing link {src} <-> {dst} at t={env.now} ***"
                    )
                    net.bring_up_link(src, dst)
                    net.bring_up_link(dst, src)

                    if algo in ["bellman_ford", "dijkstra"]:
                        log.warning(
                            f"*** CHAOS MONKEY: Recalculating routes using {algo}... ***"
                        )
                        new_tables = self.routing_algorithm(net.graph, net.links)
                        for r_id, r_obj in net.routers.items():
                            r_obj.routing_table = new_tables.get(
                                r_id, r_obj.routing_table
                            )

            env.process(chaos_monkey(env, network, failure_cfg))

        log.info("Running simulation for %.1f time units...", duration)
        env.run(until=duration)
        log.info("Simulation complete.")

        return self.collector
