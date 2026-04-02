# filename: traffic/generator.py

"""
The File Defines the Generator Function
A simpy process that genrates the packets following a Poisson arrival process
"""

import logging
import random

from simpy import Environment

from core.network import Network
from traffic.packet_factory import PacketFactory

log = logging.getLogger(__name__)


def generator(env: Environment, network: Network, config: dict):

    if "traffic" not in config:
        raise KeyError("Missing 'traffic' section in config")

    if "arrival_rate" not in config:
        raise KeyError("Missing 'arrival_rate' section in config")

    arrival_rate = config["traffic"]["arrival_rate"]
    factory = PacketFactory(config)
    router_ids = network.router_ids()

    if len(router_ids) < 2:
        log.warning("Need at least 2 routers to generate traffic.")
        return

    log.info(
        "Traffic generator started: arrival_rate=%.2f pkt/s across %d routers",
        arrival_rate,
        len(router_ids),
    )

    while True:
        inter_arrival = random.expovariate(arrival_rate)
        yield env.timeout(inter_arrival)

        source = random.choice(router_ids)
        pool = [r for r in router_ids if r != source]
        destination = random.choice(pool)

        packet = factory.create(
            source=source, destination=destination, birth_time=env.now
        )
        log.debug("%.4f  Generated %s", env.now, packet)
        network.inject(packet, at_router=source)
