# filename: queueing/red.py

"""
This File Defines the REDQueue Class
Random Early Detection. Instead of waiting for the queue to be completely full,
RED starts randomly dropping packets as queue length rises above a threshold.
Helps prevent bursty drops.
"""

import random

from queueing.base import QueueDiscipline, StatsTrackingMixin


class REDQueue(StatsTrackingMixin, QueueDiscipline):
    def __init__(
        self,
        capacity: int,
        t_min: float = 20.0,
        t_max: float = 80.0,
        p_max: float = 0.10,
        wq: float = 0.002,
        seed: int = 0,
    ) -> None:
        if not (0 < t_min < t_max <= capacity):
            raise ValueError(
                f"Need 0 < t_min ({t_min}) < t_max ({t_max}) <= capacity ({capacity})."
            )
        super().__init__(capacity=capacity)

        self.t_min = float(t_min)
        self.t_max = float(t_max)
        self.p_max = float(p_max)
        self.wq = float(wq)

        self._rng = random.Random(seed)
        self._queue: list = []

        self.lenavg: float = 0.0
        self._cnt: int = 0

    def enqueue(self, packet) -> bool:
        inst_len = len(self._queue)

        self.lenavg = (1.0 - self.wq) * self.lenavg + self.wq * inst_len

        if inst_len >= self._capacity:
            self._record_enqueue(accepted=False)
            return False

        prob = self._drop_probability()
        if prob > 0.0 and self._rng.random() < prob:
            self._cnt = 0
            self._record_enqueue(accepted=False)
            return False

        self._queue.append(packet)
        self._cnt += 1
        self._record_enqueue(accepted=True)
        return True

    def dequeue(self):
        if self.is_empty():
            return None
        packet = self._queue.pop(0)
        self._record_dequeue()
        return packet

    def is_full(self) -> bool:
        return len(self._queue) >= self._capacity

    def length(self) -> int:
        return len(self._queue)

    def _drop_probability(self) -> float:
        avg = self.lenavg

        if avg < self.t_min:
            return 0.0

        if avg >= self.t_max:
            return 1.0

        pb = self.p_max * (avg - self.t_min) / (self.t_max - self.t_min)

        deno = 1.0 - self._cnt * pb
        if deno <= 0.0:
            return 1.0
        return min(pb / deno, 1.0)
