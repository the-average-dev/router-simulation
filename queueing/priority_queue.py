"""
queueing/priority_queue.py
==========================
Priority-based queue discipline using a min-heap keyed on packet.priority.

Algorithm
---------
* Uses Python's heapq (min-heap): lowest priority value = highest urgency.
  e.g.  priority 0 → VOIP (served first)
        priority 1 → BULK
        priority 2 → BEST_EFFORT (served last)
* Tie-break on arrival sequence number so packets of equal priority are
  served FIFO among themselves (avoids non-deterministic ordering).
* Tail-drop when queue is at capacity.

No SimPy. No core/ imports. Pure data structure.
"""

from __future__ import annotations

import heapq
import itertools
from typing import Optional

from queueing.base import QueueDiscipline, StatsTrackingMixin, PacketLike


class PriorityQueue(StatsTrackingMixin, QueueDiscipline):
    """
    Min-heap priority queue.

    Lower ``packet.priority`` value = served sooner.

    Parameters
    ----------
    capacity : int
        Maximum number of packets held simultaneously (≥ 1).

    Examples
    --------
    >>> q = PriorityQueue(capacity=10)
    >>> q.enqueue(bulk_pkt)    # priority=2
    True
    >>> q.enqueue(voip_pkt)    # priority=0
    True
    >>> q.dequeue()            # returns voip_pkt first
    <Packet id=voip ...>
    """

    def __init__(self, capacity: int) -> None:
        super().__init__(capacity=capacity)
        # heap entries: (priority, sequence, packet)
        self._heap: list[tuple[int, int, PacketLike]] = []
        self._counter = itertools.count()   # monotonic sequence for tie-breaking
        self._size: int = 0

    # ------------------------------------------------------------------
    # QueueDiscipline interface
    # ------------------------------------------------------------------

    def enqueue(self, packet: PacketLike) -> bool:
        """
        Admit packet using its .priority attribute (lower = higher urgency).

        Returns
        -------
        bool
            True if admitted, False if tail-dropped.
        """
        if self.is_full():
            self._record_enqueue(accepted=False)
            return False

        seq = next(self._counter)
        heapq.heappush(self._heap, (packet.priority, seq, packet))
        self._size += 1
        self._record_enqueue(accepted=True)
        return True

    def dequeue(self) -> Optional[PacketLike]:
        """
        Remove and return the highest-priority (lowest value) packet.

        Returns None if the queue is empty.
        """
        if self.is_empty():
            return None
        _priority, _seq, packet = heapq.heappop(self._heap)
        self._size -= 1
        self._record_dequeue()
        return packet

    def is_full(self) -> bool:
        return self._size >= self._capacity

    def __len__(self) -> int:
        return self._size

    # ------------------------------------------------------------------
    # Extras
    # ------------------------------------------------------------------

    def peek(self) -> Optional[PacketLike]:
        """Return the next-to-be-served packet without removing it."""
        if self.is_empty():
            return None
        return self._heap[0][2]

    def flush(self) -> list[PacketLike]:
        """Drain the queue, returning packets in priority order."""
        result: list[PacketLike] = []
        while not self.is_empty():
            result.append(self.dequeue())
        return result
