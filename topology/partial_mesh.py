# filename: topology/partial_mesh.py


"""
This File Defines the Partial Mesh Topology Class
Like a full mesh but randomly removes some links based on a
link_probability value (0.0 to 1.0) from config.

link_probability = 1.0  -> full mesh
link_probability = 0.5  -> roughly half the links removed
link_probability = 0.3  -> sparse mesh, good for testing rerouting

Every router is guaranteed at least one link so no router
is ever completely isolated.
"""

import logging
import random

from core.network import Network
from topology.base import BaseTopology

log = logging.getLogger(__name__)


class PartialMeshTopology(BaseTopology):
    def __call__(self, network: Network, config: dict):

        if "network" not in config:
            raise KeyError("Missing 'network' section in config")

        net_cfg = config["network"]

        if "num_routers" not in net_cfg:
            raise KeyError("Missing 'num_routers' in config['network']")

        n = net_cfg["num_routers"]
        bw = net_cfg.get("link_bandwidth", 1_000_000)
        delay = net_cfg.get("link_delay", 0.002)
        probability = net_cfg.get("link_probability", 0.6)

        if n < 2:
            raise ValueError("Partial mesh needs at least 2 routers")
        if not 0.0 < probability <= 1.0:
            raise ValueError("link_probability must be between 0.0 (exclusive) and 1.0")

        router_ids = [f"R{i}" for i in range(1, n + 1)]

        for rid in router_ids:
            network.add_router(rid)

        # Track which routers have at least one link
        has_link = set()

        for i in range(len(router_ids)):
            for j in range(i + 1, len(router_ids)):
                if random.random() < probability:
                    network.add_link(
                        router_ids[i],
                        router_ids[j],
                        bandwidth=bw,
                        delay=delay,
                        bidirectional=True,
                    )
                    has_link.add(router_ids[i])
                    has_link.add(router_ids[j])
                    log.debug("Link added: %s <-> %s", router_ids[i], router_ids[j])

        for i, rid in enumerate(router_ids):
            if rid not in has_link:
                neighbour = router_ids[i - 1] if i > 0 else router_ids[1]
                network.add_link(
                    rid,
                    neighbour,
                    bandwidth=bw,
                    delay=delay,
                    bidirectional=True,
                )
                has_link.add(rid)
                log.warning(
                    "Router %s was isolated — forced link to %s", rid, neighbour
                )

        log.info("PartialMesh built: %d routers, probability=%.2f", n, probability)
