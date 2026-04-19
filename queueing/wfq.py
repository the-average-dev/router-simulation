from __future__ import annotations
import heapq
import itertools
from typing import Dict, Optional

from .base import QueueDiscipline, StatsTrackingMixin, PacketLike


DEFAULT_WEIGHTS: Dict[int, float] = {
    0: 5.0,   
    1: 2.0,   
    2: 1.0,   
}


class WFQQueue(StatsTrackingMixin, QueueDiscipline):

    def __init__(
        self,
        capacity: int,
        weights: Optional[Dict[int, float]] = None,
    ) -> None:
        super().__init__(capacity=capacity)
        self._weights: Dict[int, float] = weights if weights is not None else dict(DEFAULT_WEIGHTS)
        self._default_weight: float = 1.0

        self._heap: list[tuple[float, int, PacketLike]] = []
        self._counter = itertools.count()

        self._last_finish: Dict[int, float] = {}

        self._virtual_clock: float = 0.0
        self._size: int = 0


    def enqueue(self, packet: PacketLike) -> bool:
        
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

    def dequeue(self) -> Optional[PacketLike]:
        
        if self.is_empty():
            return None

        finish_time, _seq, packet = heapq.heappop(self._heap)
        self._virtual_clock = finish_time   # advance virtual clock
        self._size -= 1
        self._record_dequeue()
        return packet

    def is_full(self) -> bool:
        return self._size >= self._capacity

    def __len__(self) -> int:
        return self._size


    def peek(self) -> Optional[PacketLike]:
        if self.is_empty():
            return None
        return self._heap[0][2]

    def reset_virtual_clock(self) -> None:
        
        self._virtual_clock = 0.0
        self._last_finish.clear()

    @property
    def virtual_clock(self) -> float:
        return self._virtual_clock

    def flush(self) -> list[PacketLike]:
        res: list[PacketLike] = []
        while not self.is_empty():
            res.append(self.dequeue())
        return res
