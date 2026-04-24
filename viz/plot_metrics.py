# viz/plot_metrics.py

import logging
import os

import matplotlib.pyplot as plt

from metrics.collector import MetricsCollector
from metrics.per_router import PerRouterMetrics

logger = logging.getLogger(__name__)


class MetricsPlotter:
    def __init__(self, collector: MetricsCollector, out_dir="graphs"):
        self.collector = collector
        self.out_dir = out_dir
        # Auto-create the folder if it doesn't exist
        os.makedirs(self.out_dir, exist_ok=True)

    def plot_queue_length(self) -> None:
        per_router = PerRouterMetrics(self.collector)
        stats = per_router.compute()

        router_ids = sorted(stats.keys())
        num_routers = len(router_ids)

        if num_routers == 0:
            logger.debug("No router data to plot")
            return

        fig, axes = plt.subplots(
            nrows=num_routers, ncols=1, figsize=(10, 3 * num_routers), sharex=True
        )

        if num_routers == 1:
            axes = [axes]

        for ax, router_id in zip(axes, router_ids):
            timeline = stats[router_id].queue_length_over_time

            if len(timeline) == 0:
                ax.set_title(f"{router_id} — no data")
                continue

            times = [t for t, q in timeline]
            lengths = [q for t, q in timeline]

            ax.step(times, lengths, where="post", color="steelblue", linewidth=1.2)
            ax.set_title(f"Queue Length Over Time — {router_id}")
            ax.set_ylabel("Queue Length")
            ax.set_ylim(bottom=0)

        axes[-1].set_xlabel("Simulation Time (seconds)")

        # Add padding to top (y=1.02) so title doesn't overlap with the top graph
        fig.suptitle("Queue Length Over Time Per Router", fontsize=14, y=1.02)

        plt.tight_layout()
        filepath = os.path.join(self.out_dir, "queue_length_over_time.png")
        plt.savefig(filepath, bbox_inches="tight", dpi=150)
        logger.info(f"Saved graph: {filepath}")
        plt.close(fig)  # Close to prevent memory leaks

    def plot_drop_and_utilization(self) -> None:
        per_router = PerRouterMetrics(self.collector)
        stats = per_router.compute()

        router_ids = sorted(stats.keys())
        drop_rates = [stats[r].drop_rate * 100 for r in router_ids]

        # We are keeping the variable name `utilizations` to avoid breaking code,
        # but changing how it is labeled on the graph!
        utilizations = [stats[r].utilization * 100 for r in router_ids]

        x = list(range(len(router_ids)))
        width = 0.35

        fig, ax = plt.subplots(figsize=(10, 5))

        # CHANGE THE LABEL HERE: "Acceptance Rate %"
        ax.bar(
            [i - width / 2 for i in x],
            utilizations,
            width,
            label="Acceptance Rate %",
            color="steelblue",
        )
        ax.bar(
            [i + width / 2 for i in x],
            drop_rates,
            width,
            label="Drop Rate %",
            color="tomato",
        )

        # CHANGE THE TITLE HERE:
        ax.set_title("Queue Acceptance and Drop Rate Per Router")
        ax.set_xlabel("Router")
        ax.set_ylabel("Percentage (%)")
        ax.set_xticks(x)

        ax.set_xticklabels(router_ids, rotation=45, ha="right")
        ax.set_ylim(0, 115)
        ax.legend()

        plt.tight_layout()
        filepath = os.path.join(self.out_dir, "acceptance_and_drop_rate.png")
        plt.savefig(filepath, bbox_inches="tight", dpi=150)
        logger.info(f"Saved graph: {filepath}")
        plt.close(fig)
