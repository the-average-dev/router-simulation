# filename: queueing/priority_queue.py

"""
This File Defines the PriorityQueue Class
Packets are sorted by packet.priority (derived from traffic class).
VoIP packets jump the queue ahead of bulk data. Uses heapq.
"""

import heapq
import itertools

from queueing.base import QueueDiscipline, StatsTrackingMixin


class PriorityQueue(StatsTrackingMixin, QueueDiscipline):

    def __init__(self, capacity: int) -> None:
        super().__init__(capacity=capacity)
        self._heap: list = []
        self._cnt = itertools.count()
        self._size: int = 0

    def enqueue(self, packet) -> bool:
        if self.is_full():
            self._record_enqueue(accepted=False)
            return False

        seqn = next(self._cnt)
        heapq.heappush(self._heap, (packet.priority, seqn, packet))
        self._size += 1
        self._record_enqueue(accepted=True)
        return True

    def dequeue(self):
        if self.is_empty():
            return None
        _priority, _seqn, packet = heapq.heappop(self._heap)
        self._size -= 1
        self._record_dequeue()
        return packet

    def is_full(self) -> bool:
        return self._size >= self._capacity

    def length(self) -> int:
        return self._size