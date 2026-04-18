# viz/plot_metrics.py
"""
This File Defines the MetricsPlotter Class
MetricsPlotter Takes Data from PerRouterMetrics and EndToEndMetrics
and Plots Two Graphs:
    - Queue Length Over Time for Each Router
    - Throughput and Drop Rate as a Bar Chart
"""

import logging
import matplotlib.pyplot as plt
from metrics.per_router import PerRouterMetrics
from metrics.end_to_end import EndToEndMetrics
from metrics.collector import MetricsCollector

logger = logging.getLogger(__name__)


# Plots Queue Length and Throughput Graphs
class MetricsPlotter:

    # Constructor — takes the shared collector from simulation.py
    def __init__(self, collector: MetricsCollector):
        self.collector = collector

    # Plots queue length over time for every router on one graph
    def plot_queue_length(self) -> None:

        per_router = PerRouterMetrics(self.collector)
        stats = per_router.compute()

        # one subplot per router
        router_ids = sorted(stats.keys())
        num_routers = len(router_ids)

        # if no routers recorded just return
        if num_routers == 0:
            logger.debug("No router data to plot")
            return

        fig, axes = plt.subplots(
            nrows = num_routers,
            ncols = 1,
            figsize = (10, 3 * num_routers),
            sharex  = True
        )

        # if only one router axes is not a list — wrap it
        if num_routers == 1:
            axes = [axes]

        for ax, router_id in zip(axes, router_ids):

            timeline = stats[router_id].queue_length_over_time

            # nothing to plot for this router
            if len(timeline) == 0:
                ax.set_title(f"{router_id} — no data")
                continue

            # unpack list of (time, queue_length) tuples
            times   = [t for t, q in timeline]
            lengths = [q for t, q in timeline]

            ax.plot(times, lengths, color="steelblue", linewidth=1.2)
            ax.set_title(f"Queue Length Over Time — {router_id}")
            ax.set_ylabel("Queue Length (packets)")
            ax.set_ylim(bottom=0)

            logger.debug("Plotted queue length for %s", router_id)

        axes[-1].set_xlabel("Simulation Time (seconds)")
        fig.suptitle("Queue Length Over Time Per Router", fontsize=13)
        plt.tight_layout()
        plt.show()

    # Plots drop rate and utilization as a bar chart for each router
    def plot_drop_and_utilization(self) -> None:

        per_router = PerRouterMetrics(self.collector)
        stats = per_router.compute()

        router_ids = sorted(stats.keys())
        drop_rates = [stats[r].drop_rate   * 100 for r in router_ids]
        utilizations = [stats[r].utilization * 100 for r in router_ids]

        # x positions for the bars
        x = list(range(len(router_ids)))
        width = 0.35

        fig, ax = plt.subplots(figsize=(10, 5))

        # two bars side by side per router
        bars1 = ax.bar(
            [i - width / 2 for i in x],
            utilizations,
            width,
            label = "Utilization %",
            color = "steelblue"
        )
        bars2 = ax.bar(
            [i + width / 2 for i in x],
            drop_rates,
            width,
            label = "Drop Rate %",
            color = "tomato"
        )

        ax.set_title("Utilization and Drop Rate Per Router")
        ax.set_xlabel("Router")
        ax.set_ylabel("Percentage (%)")
        ax.set_xticks(x)
        ax.set_xticklabels(router_ids)
        ax.set_ylim(0, 100)
        ax.legend()

        plt.tight_layout()
        plt.show()