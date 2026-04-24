# validation/mm1.py
"""
This File Defines the MM1Queue Class
MM1Queue Computes Basic M/M/1 Analytical Formulas
Given Arrival Rate and Service Rate it Returns:
    - Utilization  rho  =  arrival_rate / service_rate
    - Average Queue Length  E[N]  =  rho / (1 - rho)
    - Average Delay  E[T]  =  1 / (service_rate - arrival_rate)
"""

import logging

logger = logging.getLogger(__name__)


# Holds the Results of M/M/1 Calculation
class MM1Result:

    # Constructor
    def __init__(
        self,
        rho: float,   # how busy the router is — between 0 and 1
        exp_queue_len: float,   # average number of packets in the router
        exp_delay: float,   # average time a packet spends in the router
    ):
        self.rho = rho
        self.exp_queue_len = exp_queue_len
        self.exp_delay = exp_delay

    # Representation of MM1Result
    def __repr__(self) -> str:
        return (
            f"MM1Result("
            f"rho={self.rho:.4f}, "
            f"E[N]={self.exp_queue_len:.4f} packets, "
            f"E[T]={self.exp_delay:.4f} sec)"
        )


# Computes M/M/1 Analytical Values
class MM1Queue:

    # Constructor
    # arrival_rate  — how many packets arrive per second
    # service_rate  — how many packets the router can handle per second
    def __init__(
        self,
        arrival_rate: float,
        service_rate: float,
    ):
        # arrival rate must be less than service rate
        # otherwise queue grows forever and formulas break
        if arrival_rate <= 0:
            raise ValueError(f"arrival_rate must be > 0, got {arrival_rate}")
        if service_rate <= 0:
            raise ValueError(f"service_rate must be > 0, got {service_rate}")
        if arrival_rate >= service_rate:
            raise ValueError(
                f"arrival_rate ({arrival_rate}) must be less than "
                f"service_rate ({service_rate})"
            )

        self.arrival_rate = arrival_rate
        self.service_rate = service_rate

        logger.debug(
            "MM1Queue: arrival_rate=%.4f service_rate=%.4f",
            arrival_rate, service_rate
        )

    # Computes rho, E[N] and E[T] and returns MM1Result
    def compute(self) -> MM1Result:

        # rho = how busy the router is
        # 0.8 means router is 80% busy
        rho = self.arrival_rate / self.service_rate

        # E[N] = average packets in the system at any moment
        exp_queue_len = rho / (1.0 - rho)

        # E[T] = average time a packet spends in the system
        exp_delay = 1.0 / (self.service_rate - self.arrival_rate)

        result = MM1Result(
            rho = rho,
            exp_queue_len = exp_queue_len,
            exp_delay = exp_delay,
        )

        logger.debug("MM1Result: %s", result)
        return result

    # Prints the results in a readable format
    def print_summary(self) -> None:
        result = self.compute()
        print(f"\nM/M/1 Analytical Results")
        print(f"Arrival Rate   : {self.arrival_rate:.4f} packets/sec")
        print(f"Service Rate   : {self.service_rate:.4f} packets/sec")
        print(f"Utilization    : {result.rho:.4f}")
        print(f"Avg Queue Len  : {result.exp_queue_len:.4f} packets")
        print(f"Avg Delay      : {result.exp_delay:.4f} seconds")