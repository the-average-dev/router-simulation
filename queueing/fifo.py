from __future__ import annotations

import collections
from typing import Optional

from .base import QueueDiscipline, StatsTrackingMixin, PacketLike

class FifoQueue(StatsTrackingMixin, QueueDiscipline):
    

    def __init__(self, capacity: int) -> None:
        super().__init__(capacity=capacity)
        self._queue: collections.deque[PacketLike] = collections.deque()



    def enqueue(self, packet: PacketLike) -> bool:
        
        if self.is_full():
            self._record_enqueue(accepted=False)
            return False

        self._queue.append(packet)
        self._record_enqueue(accepted=True)
        return True

    def dequeue(self) -> Optional[PacketLike]:
        
        if self.is_empty():
            return None
        packet = self._queue.popleft()
        self._record_dequeue()
        return packet

    def is_full(self) -> bool:
        return len(self._queue) >= self._capacity

    def __len__(self) -> int:
        return len(self._queue)



    def peek(self) -> Optional[PacketLike]:
        if self.is_empty():
            return None
        return self._queue[0]

    def flush(self) -> list[PacketLike]:
        drop = list(self._queue)
        self._queue.clear()
        return drop
