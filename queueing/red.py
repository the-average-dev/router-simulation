"""
queueing/red.py
===============
Random Early Detection (RED) active queue management discipline.

Algorithm
---------
RED maintains an *exponential weighted moving average* of the queue length
(avg_len) and uses it to compute a drop probability p:

    avg_len = (1 - w_q) * avg_len + w_q * instantaneous_len

    if avg_len < min_th:
        p = 0                          # green zone — admit all
    elif avg_len < max_th:
        p_b = max_p * (avg_len - min_th) / (max_th - min_th)
        p   = p_b / (1 - count * p_b)  # gentle increase between drops
    else:
        p = 1                          # red zone — drop all

Parameters (RFC 2309 / Floyd & Jacobson 1993)
----------------------------------------------
min_th  : lower threshold (packets).  Below this, never drop.
max_th  : upper threshold (packets).  Above this, always drop.
max_p   : maximum drop probability at max_th (typical: 0.1).
w_q     : EWMA weight for queue length smoothing (typical: 0.002).
capacity: hard maximum; tail-drop if instantaneous length hits capacity.

No SimPy. No core/ imports. Pure data structure.
"""

from __future__ import annotations

import random
from typing import Optional

from queueing.base import QueueDiscipline, StatsTrackingMixin, PacketLike, EnqueueResult


class REDQueue(StatsTrackingMixin, QueueDiscipline):
    """
    Random Early Detection queue.

    Parameters
    ----------
    capacity : int
        Hard upper limit on queue occupancy (tail-drop beyond this).
    min_th : float
        Queue length threshold below which no packets are dropped.
    max_th : float
        Queue length threshold above which all packets are dropped.
    max_p : float
        Maximum drop probability (reached at max_th). Default 0.10.
    w_q : float
        EWMA smoothing weight for avg queue length. Default 0.002.
    seed : int | None
        Random seed for reproducible simulations.

    Examples
    --------
    >>> q = REDQueue(capacity=100, min_th=20, max_th=80, max_p=0.1)
    >>> accepted = q.enqueue(pkt)   # may be False due to RED drop
    >>> result   = q.enqueue_detailed(pkt)   # EnqueueResult with reason
    """

    def __init__(
        self,
        capacity: int,
        min_th: float = 20.0,
        max_th: float = 80.0,
        max_p: float = 0.10,
        w_q: float = 0.002,
        seed: Optional[int] = None,
    ) -> None:
        if not (0 < min_th < max_th <= capacity):
            raise ValueError(
                f"Need 0 < min_th ({min_th}) < max_th ({max_th}) <= capacity ({capacity})."
            )
        super().__init__(capacity=capacity)

        self.min_th = float(min_th)
        self.max_th = float(max_th)
        self.max_p  = float(max_p)
        self.w_q    = float(w_q)

        self._rng = random.Random(seed)
        self._queue: list[PacketLike] = []

        # RED state
        self._avg_len: float = 0.0   # EWMA of queue length
        self._count: int = 0         # packets since last RED drop

    # ------------------------------------------------------------------
    # QueueDiscipline interface
    # ------------------------------------------------------------------

    def enqueue(self, packet: PacketLike) -> bool:
        """Admit or drop the packet using RED logic. Returns True if admitted."""
        return bool(self.enqueue_detailed(packet))

    def enqueue_detailed(self, packet: PacketLike) -> EnqueueResult:
        """
        Same as enqueue() but returns an EnqueueResult with drop reason.
        """
        inst_len = len(self._queue)

        # 1. Update EWMA
        self._avg_len = (1.0 - self.w_q) * self._avg_len + self.w_q * inst_len

        # 2. Hard tail-drop (queue physically full)
        if inst_len >= self._capacity:
            self._record_enqueue(accepted=False)
            return EnqueueResult(accepted=False, reason="tail_drop")

        # 3. RED drop decision
        drop_prob = self._drop_probability()
        if drop_prob > 0.0 and self._rng.random() < drop_prob:
            self._count = 0          # reset inter-drop counter
            self._record_enqueue(accepted=False)
            return EnqueueResult(accepted=False, reason="red_drop")

        # 4. Admit
        self._queue.append(packet)
        self._count += 1
        self._record_enqueue(accepted=True)
        return EnqueueResult(accepted=True, reason="admitted")

    def dequeue(self) -> Optional[PacketLike]:
        """Remove and return the oldest packet (FIFO within RED)."""
        if self.is_empty():
            return None
        packet = self._queue.pop(0)
        self._record_dequeue()
        return packet

    def is_full(self) -> bool:
        """True when instantaneous queue length has hit hard capacity."""
        return len(self._queue) >= self._capacity

    def __len__(self) -> int:
        return len(self._queue)

    # ------------------------------------------------------------------
    # RED internals
    # ------------------------------------------------------------------

    def _drop_probability(self) -> float:
        """
        Compute instantaneous RED drop probability from avg_len.

        Returns a value in [0.0, 1.0].
        """
        avg = self._avg_len

        if avg < self.min_th:
            return 0.0

        if avg >= self.max_th:
            return 1.0

        # Linear interpolation zone
        p_b = self.max_p * (avg - self.min_th) / (self.max_th - self.min_th)

        # Gentle increase: avoid burst of drops
        denom = 1.0 - self._count * p_b
        if denom <= 0.0:
            return 1.0
        return min(p_b / denom, 1.0)

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    @property
    def avg_queue_len(self) -> float:
        """Current EWMA-smoothed average queue length."""
        return self._avg_len

    @property
    def current_drop_probability(self) -> float:
        """Drop probability based on the current avg queue length."""
        return self._drop_probability()

    def flush(self) -> list[PacketLike]:
        """Drain all packets without RED logic."""
        result = list(self._queue)
        self._queue.clear()
        return result
