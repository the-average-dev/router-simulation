# viz/plot_delay_cdf.py

import logging
import os

import matplotlib.pyplot as plt

from metrics.collector import MetricsCollector

logger = logging.getLogger(__name__)


class DelayCDFPlotter:
    def __init__(self, collector: MetricsCollector, out_dir="graphs"):
        self.collector = collector
        self.out_dir = out_dir
        os.makedirs(self.out_dir, exist_ok=True)

    def plot_cdf(self, split_by_type: bool = False) -> None:
        deliveries = self.collector.deliveries

        if len(deliveries) == 0:
            logger.debug("No delivery data to plot")
            return

        fig, ax = plt.subplots(figsize=(10, 5))

        if split_by_type:
            delays_by_type: dict[str, list[float]] = {}
            for event in deliveries:
                t = event.traffic_type
                if t not in delays_by_type:
                    delays_by_type[t] = []
                delays_by_type[t].append(event.extra["delay"])

            colors = {"voip": "steelblue", "bulk": "tomato", "best_effort": "seagreen"}

            for traffic_type, delays in sorted(delays_by_type.items()):
                sorted_delays = sorted(delays)
                n = len(sorted_delays)
                cdf_y = [(i + 1) / n for i in range(n)]

                ax.plot(
                    sorted_delays,
                    cdf_y,
                    label=traffic_type,
                    color=colors.get(traffic_type, "gray"),
                    linewidth=2.0,  # Made line thicker
                )

            ax.legend(
                title="Traffic Type", loc="lower right"
            )  # Move legend out of the way of the curves

        else:
            all_delays = [event.extra["delay"] for event in deliveries]
            sorted_delays = sorted(all_delays)
            n = len(sorted_delays)
            cdf_y = [(i + 1) / n for i in range(n)]
            ax.plot(sorted_delays, cdf_y, color="steelblue", linewidth=2.0)

        ax.set_title("CDF of End to End Packet Delay")
        ax.set_xlabel("Delay (seconds)")
        ax.set_ylabel("Fraction of Packets")
        ax.set_ylim(0, 1.05)
        ax.set_xlim(left=0)
        ax.grid(True, linestyle="--", alpha=0.5)  # Added grid for readability

        # helpful reference lines
        ax.axhline(
            y=0.5, color="gray", linestyle="--", linewidth=0.8, label="50th percentile"
        )
        ax.axhline(
            y=0.95, color="gray", linestyle=":", linewidth=0.8, label="95th percentile"
        )

        plt.tight_layout()

        filename = "delay_cdf_split.png" if split_by_type else "delay_cdf_combined.png"
        filepath = os.path.join(self.out_dir, filename)

        plt.savefig(filepath, bbox_inches="tight", dpi=150)
        logger.info(f"Saved graph: {filepath}")
        plt.close(fig)
