# filename: topology/tree.py


"""
Routers arranged as a complete binary tree using binary heap indexing.
Each parent connects to two children. Does not require a perfect power of 2.
"""

import logging

from core.network import Network
from topology.base import BaseTopology

log = logging.getLogger(__name__)


class TreeTopology(BaseTopology):
    def __call__(self, network: Network, config: dict):
        if "network" not in config:
            raise KeyError("Missing 'network' section in config")

        net_cfg = config["network"]

        if "num_routers" not in net_cfg:
            raise KeyError("Missing 'num_routers' in config['network']")

        n = net_cfg["num_routers"]
        bw = net_cfg.get("link_bandwidth", 1_000_000)
        delay = net_cfg.get("link_delay", 0.002)

        if n < 1:
            raise ValueError("Tree topology needs at least 1 router")

        router_ids = [f"R{i}" for i in range(1, n + 1)]

        for rid in router_ids:
            network.add_router(rid)

        # Connect each node to its parent using 0-based binary heap indexing
        for i in range(1, n):
            child = router_ids[i]
            parent = router_ids[(i - 1) // 2]
            network.add_link(
                parent,
                child,
                bandwidth=bw,
                delay=delay,
                bidirectional=True,
            )
            log.debug("Tree link: %s <-> %s", parent, child)

        depth = n.bit_length() - 1
        log.info("Tree built: %d routers, depth=%d", n, depth)

