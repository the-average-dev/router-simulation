# filename: topology/star.py

"""
This File Defines the Star Topology Class
One central hub router (R1) connected to N spoke routers.
Spokes only connect to the hub, never to each other.
"""

import logging

from core.network import Network
from topology.base import BaseTopology

log = logging.getLogger(__name__)


class StarTopology(BaseTopology):
    def __call__(self, network: Network, config: dict):
        if "network" not in config:
            raise KeyError("Missing 'network' section in config")

        net_cfg = config["network"]

        if "num_routers" not in net_cfg:
            raise KeyError("Missing 'num_routers' in config['network']")

        n = net_cfg["num_routers"]
        bw = net_cfg.get("link_bandwidth", 1_000_000)
        delay = net_cfg.get("link_delay", 0.002)

        if n < 2:
            raise ValueError("Star topology needs at least 2 routers (1 hub + 1 spoke)")

        router_ids = [f"R{i}" for i in range(1, n + 1)]
        hub = router_ids[0]
        spokes = router_ids[1:]

        network.add_router(hub)

        for spoke in spokes:
            network.add_router(spoke)
            network.add_link(hub, spoke, bandwidth=bw, delay=delay, bidirectional=True)
            log.debug("Star link: %s <-> %s", hub, spoke)

        log.info("Star built: hub=%s, %d spokes", hub, len(spokes))
