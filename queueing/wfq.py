"""
queueing/wfq.py
===============
Weighted Fair Queueing (WFQ) discipline.

Algorithm — Virtual Clock / Finish-Time WFQ
--------------------------------------------
Each traffic class gets a *weight* (e.g. VOIP=5, BULK=2, BEST_EFFORT=1).
When a packet of class C with size B bytes arrives, its virtual finish time is:

    F_i = max(F_{i-1}, virtual_clock) + B / weight_C

where virtual_clock advances to the finish time of the last served packet.
dequeue() always picks the packet with the smallest virtual finish time —
this approximates GPS (Generalised Processor Sharing) and gives each class
throughput proportional to its weight under congestion.

Separate per-class FIFOs are maintained so the heap entry stores
(virtual_finish_time, seq, packet).  Total queue depth is capped at
``capacity`` packets across all classes.

No SimPy. No core/ imports. Pure data structure.
"""

from __future__ import annotations

import heapq
import itertools
from typing import Dict, Optional

from queueing.base import QueueDiscipline, StatsTrackingMixin, PacketLike

# Default weights if the caller doesn't supply a mapping.
# Keys should match packet.priority (int) or a traffic-class label.
DEFAULT_WEIGHTS: Dict[int, float] = {
    0: 5.0,   # VOIP / highest priority
    1: 2.0,   # BULK
    2: 1.0,   # BEST_EFFORT
}


class WFQQueue(StatsTrackingMixin, QueueDiscipline):
    """
    Weighted Fair Queueing.

    Parameters
    ----------
    capacity : int
        Total packet capacity across all classes.
    weights : dict[int, float], optional
        Mapping of packet.priority → weight.  Higher weight = more bandwidth.
        Defaults to {0: 5.0, 1: 2.0, 2: 1.0}.

    Examples
    --------
    >>> q = WFQQueue(capacity=100, weights={0: 4, 1: 2, 2: 1})
    >>> q.enqueue(voip_pkt)   # priority=0, size=160
    True
    >>> q.enqueue(bulk_pkt)   # priority=1, size=1500
    True
    >>> q.dequeue()           # voip_pkt served first (lower virtual finish time)
    """

    def __init__(
        self,
        capacity: int,
        weights: Optional[Dict[int, float]] = None,
    ) -> None:
        super().__init__(capacity=capacity)
        self._weights: Dict[int, float] = weights if weights is not None else dict(DEFAULT_WEIGHTS)
        self._default_weight: float = 1.0

        # Heap: (virtual_finish_time, seq, packet)
        self._heap: list[tuple[float, int, PacketLike]] = []
        self._counter = itertools.count()

        # Per-class last finish time (virtual clock per class)
        self._last_finish: Dict[int, float] = {}

        # Global virtual clock — advances when a packet is dequeued
        self._virtual_clock: float = 0.0
        self._size: int = 0

    # ------------------------------------------------------------------
    # QueueDiscipline interface
    # ------------------------------------------------------------------

    def enqueue(self, packet: PacketLike) -> bool:
        """
        Compute virtual finish time and insert into the WFQ heap.

        Returns
        -------
        bool
            True if admitted, False if tail-dropped (total capacity exceeded).
        """
        if self.is_full():
            self._record_enqueue(accepted=False)
            return False

        cls = packet.priority
        weight = self._weights.get(cls, self._default_weight)
        size = getattr(packet, "size", 1)          # fallback to 1 if no size attr

        # Virtual finish time for this packet
        last = self._last_finish.get(cls, self._virtual_clock)
        finish_time = max(last, self._virtual_clock) + size / weight
        self._last_finish[cls] = finish_time

        seq = next(self._counter)
        heapq.heappush(self._heap, (finish_time, seq, packet))
        self._size += 1
        self._record_enqueue(accepted=True)
        return True

    def dequeue(self) -> Optional[PacketLike]:
        """
        Serve the packet with the smallest virtual finish time.

        Advances the global virtual clock to that finish time.
        Returns None if the queue is empty.
        """
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

    # ------------------------------------------------------------------
    # Extras
    # ------------------------------------------------------------------

    def peek(self) -> Optional[PacketLike]:
        """Return the next packet to be served without removing it."""
        if self.is_empty():
            return None
        return self._heap[0][2]

    def reset_virtual_clock(self) -> None:
        """
        Reset the virtual clock and per-class state.
        Call between simulation warm-up and measurement phases.
        """
        self._virtual_clock = 0.0
        self._last_finish.clear()

    @property
    def virtual_clock(self) -> float:
        return self._virtual_clock

    def flush(self) -> list[PacketLike]:
        """Drain all packets in WFQ order."""
        result: list[PacketLike] = []
        while not self.is_empty():
            result.append(self.dequeue())
        return result
