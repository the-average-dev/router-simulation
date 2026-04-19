# filename: traffic/packet_factory

"""
The File Defines the PacketFactory Class
Creates Packet objects with randomised size and traffic class.
"""

import logging
import random

from core.packet import Packet
from traffic.traffic_classes import TrafficClass

log = logging.getLogger(__name__)


class PacketFactory:
    # constructor
    def __init__(self, config: dict):

        if "traffic" not in config:
            raise KeyError("Missing 'traffic' section in config")

        traffic_cfg = config["traffic"]

        self.classes = traffic_cfg.get("classes", TrafficClass.ALL)

        self.weights = traffic_cfg.get(
            "class_weights", [1.0 / len(self.classes)] * len(self.classes)
        )
        self.mean_size = traffic_cfg.get("packet_size_mean", 512)
        self.counter = 0

        # Create a packet

    def create(self, source, destination, birth_time):

        self.counter += 1
        traffic_class = random.choices(self.classes, weights=self.weights, k=1)[0]

        mean_size = TrafficClass.MEAN_SIZE.get(traffic_class, self.mean_size)

        size = int(max(64, min(1500, random.expovariate(1.0 / mean_size))))  

        return Packet(
            id=self.counter,
            size=size,
            source=source,
            destination=destination,
            traffic_type=traffic_class,
            arrival_time=birth_time,
        )
