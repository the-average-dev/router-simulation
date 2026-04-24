# viz/plot_delay_cdf.py
"""
This File Defines the DelayCDFPlotter Class
DelayCDFPlotter Takes Delivery Data from MetricsCollector and Plots
a CDF of End to End Delay Across All Delivered Packets

CDF — Cumulative Distribution Function
It Shows What Percentage of Packets Were Delivered Within X Seconds
Example: 80% of packets were delivered within 5 seconds
"""

import logging
import matplotlib.pyplot as plt
from metrics.collector import MetricsCollector

logger = logging.getLogger(__name__)


# Plots CDF of End to End Packet Delay
class DelayCDFPlotter:

    # Constructor — takes the shared collector from simulation.py
    def __init__(self, collector: MetricsCollector):
        self.collector = collector

    # Plots the CDF of delay for all delivered packets
    # Optionally split by traffic type — voip, bulk, best_effort
    def plot_cdf(self, split_by_type: bool = False) -> None:

        deliveries = self.collector.deliveries

        # nothing to plot if no packets were delivered
        if len(deliveries) == 0:
            logger.debug("No delivery data to plot")
            return

        fig, ax = plt.subplots(figsize=(10, 5))

        if split_by_type:
            # group delays by traffic type
            delays_by_type: dict[str, list[float]] = {}

            for event in deliveries:
                t = event.traffic_type
                if t not in delays_by_type:
                    delays_by_type[t] = []
                delays_by_type[t].append(event.extra["delay"])

            # one CDF line per traffic type
            colors = {"voip": "steelblue", "bulk": "tomato", "best_effort": "seagreen"}

            for traffic_type, delays in sorted(delays_by_type.items()):

                # sort delays to build CDF
                sorted_delays = sorted(delays)
                n = len(sorted_delays)

                # y axis — what fraction of packets have delay <= x
                cdf_y = [(i + 1) / n for i in range(n)]

                ax.plot(
                    sorted_delays,
                    cdf_y,
                    label     = traffic_type,
                    color     = colors.get(traffic_type, "gray"),
                    linewidth = 1.5
                )

                logger.debug("Plotted CDF for traffic type %s", traffic_type)

            ax.legend(title="Traffic Type")

        else:
            # single CDF line for all packets combined
            all_delays = [event.extra["delay"] for event in deliveries]
            sorted_delays = sorted(all_delays)
            n = len(sorted_delays)
            cdf_y = [(i + 1) / n for i in range(n)]

            ax.plot(sorted_delays, cdf_y, color="steelblue", linewidth=1.5)

            logger.debug("Plotted combined CDF for %d packets", n)

        ax.set_title("CDF of End to End Packet Delay")
        ax.set_xlabel("Delay (seconds)")
        ax.set_ylabel("Fraction of Packets")
        ax.set_ylim(0, 1.05)
        ax.set_xlim(left=0)

        # helpful reference lines
        ax.axhline(y=0.5,  color="gray", linestyle="--", linewidth=0.8, label="50th percentile")
        ax.axhline(y=0.95, color="gray", linestyle=":",  linewidth=0.8, label="95th percentile")

        plt.tight_layout()
        plt.show()