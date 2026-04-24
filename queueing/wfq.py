# filename: queueing/wfq.py

"""
This File Defines the WFQQueue Class
Weighted Fair Queueing. Each traffic class has a weight.
The virtual clock scheduler ensures each class gets its share
of bandwidth proportionally.
Priority keys match core/packet.py CLASS_PRIORITY: voip=1, bulk=2, best_effort=3.
"""

import heapq
import itertools

from queueing.base import QueueDiscipline, StatsTrackingMixin

DEFAULT_WEIGHTS: dict = {
    1: 5.0,  # voip
    2: 2.0,  # bulk
    3: 1.0,  # best_effort
}


class WFQQueue(StatsTrackingMixin, QueueDiscipline):
    def __init__(
        self,
        capacity: int,
        weights: dict | None = None,
    ) -> None:
        super().__init__(capacity=capacity)
        self._weights: dict = weights if weights is not None else dict(DEFAULT_WEIGHTS)
        self._default_weight: float = 1.0

        self._heap: list = []
        self._counter = itertools.count()

        self._last_finish: dict = {}
        self._virtual_clock: float = 0.0
        self._size: int = 0

    def enqueue(self, packet) -> bool:
        if self.is_full():
            self._record_enqueue(accepted=False)
            return False

        cls = packet.priority
        weight = self._weights.get(cls, self._default_weight)
        size = getattr(packet, "size", 1)

        last = self._last_finish.get(cls, self._virtual_clock)
        finish_time = max(last, self._virtual_clock) + size / weight
        self._last_finish[cls] = finish_time

        seq = next(self._counter)
        heapq.heappush(self._heap, (finish_time, seq, packet))
        self._size += 1
        self._record_enqueue(accepted=True)
        return True

    def dequeue(self):
        if self.is_empty():
            return None

        finish_time, _seq, packet = heapq.heappop(self._heap)
        self._virtual_clock = finish_time
        self._size -= 1
        self._record_dequeue()
        return packet

    def is_full(self) -> bool:
        return self._size >= self._capacity

    def length(self) -> int:
        return self._size
