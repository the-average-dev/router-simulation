# filename: topology/ring.py

"""
This File Defines the Ring Topology Class
Each router connects only to its two immediate neighbours
forming a closed circle:
"""

import logging

from topology.base import BaseTopology
from core.network import Network

log = logging.getLogger(__name__)


class RingTopology(BaseTopology):

    def __call__(self, network:Network, config:dict):
        
        if "network" not in config:
            raise KeyError("Missing 'network' section in config")

        net_cfg = config["network"]

        if "num_routers" not in net_cfg:
            raise KeyError("Missing 'num_routers' in config['network']")

        n     = net_cfg["num_routers"]
        bw    = net_cfg.get("link_bandwidth", 1_000_000)
        delay = net_cfg.get("link_delay", 0.002)

        if n < 3:
            raise ValueError("Ring topology needs at least 3 routers")

        router_ids = [f"R{i}" for i in range(1, n + 1)]

        for rid in router_ids:
            network.add_router(rid)

        # Connect each router to the next, and wrap last back to first
        for i in range(n):
            src = router_ids[i]
            dst = router_ids[(i + 1) % n]
            network.add_link(src, dst, bandwidth=bw, delay=delay, bidirectional=True)
            log.debug("Ring link: %s <-> %s", src, dst)

        log.info("Ring built: %d routers", n)