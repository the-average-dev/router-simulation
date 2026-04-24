# filename: topology/base.py

"""
This File Define the Base Class for topology builder
It will recive network class and config and build a Topology
"""

from core.network import Network


class BaseTopology:
    # This must be override by subclass
    def __call__(self, network: Network, config: dict):

        raise NotImplementedError(
            f"{self.__class__.__name__} must implement __call__(network, config)"
        )
