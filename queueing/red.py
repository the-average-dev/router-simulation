from __future__ import annotations
import random
from typing import Optional
from .base import QueueDiscipline, StatsTrackingMixin, PacketLike, EnqueueResult


class REDQueue(StatsTrackingMixin, QueueDiscipline):

    def __init__(
        self,
        capacity: int,
        t_min: float = 20.0,
        t_max: float = 80.0,
        p_max: float = 0.10,
        wq: float = 0.002,
        seed: Optional[int] = None,
    ) -> None:
        if not (0 < t_min < t_max <= capacity):
            raise ValueError(
                f"Need 0 < t_min ({t_min}) < t_max ({t_max}) <= capacity ({capacity})."
            )
        super().__init__(capacity=capacity)

        self.t_min = float(t_min)
        self.t_max = float(t_max)
        self.p_max  = float(p_max)
        self.wq    = float(wq)

        self.range = random.Random(seed)
        self.queue: list[PacketLike] = []

        self.lenavg: float = 0.0   
        self.cnt: int = 0         


    def enqueue(self, packet: PacketLike) -> bool:
        return bool(self.enqueue_detailed(packet))

    def enqueue_detailed(self, packet: PacketLike) -> EnqueueResult:
        
        inst_len = len(self.queue)

        self.lenavg = (1.0 - self.wq) * self.lenavg + self.wq * inst_len

        if inst_len >= self._capacity:
            self._record_enqueue(accepted=False)
            return EnqueueResult(accepted=False, reason="tail_drop")

        prob = self._drop_probability()
        if prob > 0.0 and self.range.random() < prob:
            self.cnt = 0          # reset inter-drop counter
            self._record_enqueue(accepted=False)
            return EnqueueResult(accepted=False, reason="red_drop")

        self.queue.append(packet)
        self.cnt += 1
        self._record_enqueue(accepted=True)
        return EnqueueResult(accepted=True, reason="admitted")

    def dequeue(self) -> Optional[PacketLike]:
        if self.is_empty():
            return None
        packet = self.queue.pop(0)
        self._record_dequeue()
        return packet

    def is_full(self) -> bool:
        return len(self.queue) >= self._capacity

    def __len__(self) -> int:
        return len(self.queue)


    def _drop_probability(self) -> float:
        avg = self.lenavg

        if avg < self.t_min:
            return 0.0

        if avg >= self.t_max:
            return 1.0

        pb = self.p_max * (avg - self.t_min) / (self.t_max - self.t_min)

        deno = 1.0 - self.cnt * pb
        if deno <= 0.0:
            return 1.0
        return min(pb / deno, 1.0)

    @property
    def avg_queue_len(self) -> float:
        return self.lenavg

    @property
    def current_drop_probability(self) -> float:
        return self._drop_probability()

    def flush(self) -> list[PacketLike]:
        res = list(self.queue)
        self.queue.clear()
        return res
