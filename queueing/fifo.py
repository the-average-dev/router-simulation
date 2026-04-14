"""
queueing/fifo.py
================
First-In First-Out queue discipline with tail-drop on overflow.

Algorithm
---------
* Backed by collections.deque for O(1) append (enqueue) and popleft (dequeue).
* When the queue is full, any arriving packet is silently dropped (tail-drop).
* Inherits StatsTrackingMixin for free enqueued/dropped/dequeued counters.

No SimPy. No core/ imports. Pure data structure.
"""

from __future__ import annotations

import collections
from typing import Optional

from queueing.base import QueueDiscipline, StatsTrackingMixin, PacketLike


class FifoQueue(StatsTrackingMixin, QueueDiscipline):
    """
    Classic FIFO (tail-drop) queue.

    Parameters
    ----------
    capacity : int
        Maximum number of packets held simultaneously (≥ 1).

    Examples
    --------
    >>> q = FifoQueue(capacity=4)
    >>> q.enqueue(pkt_a)
    True
    >>> q.dequeue()
    <Packet id=pkt_a ...>
    """

    def __init__(self, capacity: int) -> None:
        super().__init__(capacity=capacity)
        self._queue: collections.deque[PacketLike] = collections.deque()

    # ------------------------------------------------------------------
    # QueueDiscipline interface
    # ------------------------------------------------------------------

    def enqueue(self, packet: PacketLike) -> bool:
        """
        Admit packet if space is available; tail-drop otherwise.

        Returns
        -------
        bool
            True if admitted, False if dropped.
        """
        if self.is_full():
            self._record_enqueue(accepted=False)
            return False

        self._queue.append(packet)
        self._record_enqueue(accepted=True)
        return True

    def dequeue(self) -> Optional[PacketLike]:
        """
        Return and remove the oldest packet (FIFO order).

        Returns None if the queue is empty.
        """
        if self.is_empty():
            return None
        packet = self._queue.popleft()
        self._record_dequeue()
        return packet

    def is_full(self) -> bool:
        return len(self._queue) >= self._capacity

    def __len__(self) -> int:
        return len(self._queue)

    # ------------------------------------------------------------------
    # Extras
    # ------------------------------------------------------------------

    def peek(self) -> Optional[PacketLike]:
        """Return the head-of-line packet without removing it."""
        if self.is_empty():
            return None
        return self._queue[0]

    def flush(self) -> list[PacketLike]:
        """Remove and return all packets (e.g. on link failure)."""
        dropped = list(self._queue)
        self._queue.clear()
        return dropped
