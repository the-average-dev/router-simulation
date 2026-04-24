from __future__ import annotations
import heapq
import itertools
from typing import Optional

from .base import QueueDiscipline, StatsTrackingMixin, PacketLike


class PriorityQueue(StatsTrackingMixin, QueueDiscipline):

    def __init__(self, capacity: int) -> None:
        super().__init__(capacity=capacity)
        self.heap: list[tuple[int, int, PacketLike]] = []
        self.cnt = itertools.count()
        self.size: int = 0


    def enqueue(self, packet: PacketLike) -> bool:
        
        if self.is_full():
            self._record_enqueue(accepted=False)
            return False

        seqn = next(self.cnt)
        heapq.heappush(self._heap, (packet.priority, seqn, packet))
        self.size += 1
        self._record_enqueue(accepted=True)
        return True

    def dequeue(self) -> Optional[PacketLike]:
        
        if self.is_empty():
            return None
        _priority, _seqn, packet = heapq.heappop(self._heap)
        self.size -= 1
        self._record_dequeue()
        return packet

    def is_full(self) -> bool:
        return self.size >= self._capacity

    def __len__(self) -> int:
        return self.size


    def peek(self) -> Optional[PacketLike]:
        if self.is_empty():
            return None
        return self._heap[0][2]

    def flush(self) -> list[PacketLike]:
        res: list[PacketLike] = []
        while not self.is_empty():
            res.append(self.dequeue())
        return res
