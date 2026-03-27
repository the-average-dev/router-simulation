# filename: core/simulation.py


"""
This File Define the Top Simulation Class
Simulation Class starts and handle the simulation
"""


import logging
import random
import simpy
import json

from core.network import Network
from metrics.collector import MetricsCollector

log = logging.getLogger(__name__)


class Simulation:
    
    # Constructor
    def __init__(
        self,
        config:dict,
        topology_factory,
        queue_factory,
        routing_algorithm,
        traffic_generator,
        collector: MetricsCollector | None=None,
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
        
        # TODO build the topology one implenmented topology factory nad genreate traffic and start simulation
 
    # load a json config file and return as dict
    def load_config(self,path: str) -> dict:
        try:
            with open(path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file not found: {path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in config file: {path}")
        except Exception as e:
            raise RuntimeError(f"Error loading config: {e}")
        