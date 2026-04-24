# filename: topology/linear.py


"""
This File Defines the Linear Topology Class
It builds a bidirectional linear chain of N routers
"""

import logging

from core.network import Network
from topology.base import BaseTopology

log = logging.getLogger(__name__)

class LinearTopology(BaseTopology):
    def __call__(self, network: Network, config: dict):

        if "network" not in config:
            raise KeyError("Missing 'network' section in config")

        net_cfg = config["network"]
        
        if "num_routers" not in net_cfg:
            raise KeyError("Missing 'num_routers' section in config")


        net_cfg = config["network"]
        n = net_cfg["num_routers"]
        bw = net_cfg.get("link_bandwidth", 1_000_000)
        delay = net_cfg.get("link_delay", 0.002)

        router_ids = [f"R{i}" for i in range(1, n + 1)]

        for rid in router_ids:
            network.add_router(rid)

        for i in range(len(router_ids) - 1):
            network.add_link(
                router_ids[i],
                router_ids[i + 1],
                bandwidth=bw,
                delay=delay,
                bidirectional=True,
            )
            log.debug("Link added: %s <-> %s", router_ids[i], router_ids[i+1])

        log.info("Linear Topology built: %d routers", n)