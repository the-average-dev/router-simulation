# filename: queueing/fifo.py

"""
This File Defines the FifoQueue Class
First-In First-Out queue. Drops tail when queue is full.
Simplest discipline — baseline for M/M/1 validation.
"""

import collections

from queueing.base import QueueDiscipline, StatsTrackingMixin


class FifoQueue(StatsTrackingMixin, QueueDiscipline):
    def __init__(self, capacity: int) -> None:
        super().__init__(capacity=capacity)
        self._queue: collections.deque = collections.deque()

    def enqueue(self, packet) -> bool:
        if self.is_full():
            self._record_enqueue(accepted=False)
            return False

        self._queue.append(packet)
        self._record_enqueue(accepted=True)
        return True

    def dequeue(self):
        if self.is_empty():
            return None
        packet = self._queue.popleft()
        self._record_dequeue()
        return packet

    def is_full(self) -> bool:
        return len(self._queue) >= self._capacity

    def length(self) -> int:
        return len(self._queue)
