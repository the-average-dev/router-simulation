"""
queueing/base.py
================
Abstract base class (contract) for all queue disciplines in the router simulation.

Design rules
------------
* NO SimPy imports — this is a pure data-structure layer.
* NO dependency on core/ — works completely standalone.
* Every concrete discipline (FIFO, PQ, WFQ, RED …) inherits from QueueDiscipline
  and must implement the three abstract methods below.
* The SimPy wiring that calls enqueue() / dequeue() lives in router.py (Person A's file).

Packet contract
---------------
The methods below expect objects that expose at least:
    packet.id         : any hashable — unique packet identifier
    packet.size       : int | float — bytes (used by WFQ for byte-weighted scheduling)
    packet.priority   : int — lower value = higher urgency  (used by PriorityQueue)
    packet.birth_time : float — simulation timestamp at creation (used by metrics)

Feel free to pass a dataclass, a namedtuple, or a plain object — as long as those
attributes exist, the disciplines will work.
"""

from __future__ import annotations

import abc
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Type alias — keeps signatures readable without importing the real Packet
# ---------------------------------------------------------------------------
PacketLike = Any   # duck-typed: must have .id, .size, .priority, .birth_time


class QueueDiscipline(abc.ABC):
    """
    Abstract contract for every queue discipline.

    Parameters
    ----------
    capacity : int
        Maximum number of packets the queue may hold at one time.
        Use -1 (or math.inf) to signal an unbounded queue, though
        concrete implementations may choose not to support that.
    """

    def __init__(self, capacity: int) -> None:
        if capacity == 0:
            raise ValueError("capacity must be ≥ 1 (or -1 for unbounded).")
        self._capacity: int = capacity

    # ------------------------------------------------------------------
    # Abstract interface — every subclass MUST implement these three
    # ------------------------------------------------------------------

    @abc.abstractmethod
    def enqueue(self, packet: PacketLike) -> bool:
        """
        Attempt to add *packet* to the queue.

        Parameters
        ----------
        packet : PacketLike
            The packet to admit.

        Returns
        -------
        bool
            True  — packet was accepted and is now in the queue.
            False — packet was dropped (tail-drop, RED drop, etc.).

        Notes
        -----
        Implementations decide their own drop policy:
          * FIFO  → tail-drop when len == capacity
          * RED   → probabilistic early drop based on avg queue length
          * Token bucket → drop / shape when tokens are exhausted
        """

    @abc.abstractmethod
    def dequeue(self) -> Optional[PacketLike]:
        """
        Remove and return the next packet according to this discipline.

        Returns
        -------
        PacketLike
            The packet chosen by the scheduling policy.
        None
            If the queue is currently empty.

        Notes
        -----
        Ordering semantics differ per discipline:
          * FIFO          → oldest packet first
          * PriorityQueue → lowest priority value first
          * WFQ           → packet whose flow has the smallest virtual finish time
        """

    @abc.abstractmethod
    def is_full(self) -> bool:
        """
        Return True if the queue cannot accept any more packets right now.

        Used by router.py to decide whether to call enqueue() at all,
        and by metrics/collector.py to record saturation events.
        """

    # ------------------------------------------------------------------
    # Concrete helpers — available to all subclasses for free
    # ------------------------------------------------------------------

    def is_empty(self) -> bool:
        """Return True when there are no packets waiting to be served."""
        return self.__len__() == 0

    @property
    def capacity(self) -> int:
        """Maximum number of packets this queue can hold."""
        return self._capacity

    @abc.abstractmethod
    def __len__(self) -> int:
        """Current number of packets in the queue."""

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"capacity={self._capacity}, "
            f"occupancy={len(self)})"
        )


# ---------------------------------------------------------------------------
# Lightweight result type — returned by enqueue() when you need richer info
# ---------------------------------------------------------------------------

class EnqueueResult:
    """
    Optional richer return value for enqueue().

    Concrete disciplines may return this instead of a plain bool when
    the metrics collector needs to record *why* a packet was dropped.

    Usage (optional — FIFO just returns bool):
        result = queue.enqueue(pkt)
        if not result.accepted:
            stats.record_drop(result.reason)
    """

    __slots__ = ("accepted", "reason")

    REASONS = frozenset({
        "tail_drop",       # queue full, packet discarded at the tail
        "red_drop",        # RED probabilistic early drop
        "token_exhausted", # token bucket had no tokens available
        "admitted",        # no drop
    })

    def __init__(self, accepted: bool, reason: str = "admitted") -> None:
        if reason not in self.REASONS:
            raise ValueError(f"Unknown drop reason '{reason}'. Valid: {self.REASONS}")
        self.accepted: bool = accepted
        self.reason: str = reason

    def __bool__(self) -> bool:          # lets callers do: if queue.enqueue(pkt):
        return self.accepted

    def __repr__(self) -> str:
        return f"EnqueueResult(accepted={self.accepted}, reason={self.reason!r})"


# ---------------------------------------------------------------------------
# Mixin: optional stats tracking (plug in via multiple inheritance)
# ---------------------------------------------------------------------------

class StatsTrackingMixin:
    """
    Optional mixin that adds lightweight drop / throughput counters.

    Usage:
        class FifoQueue(StatsTrackingMixin, QueueDiscipline):
            ...

    Then call self._record_enqueue(accepted) inside enqueue(), and
    read self.stats at any time.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._enqueued: int = 0
        self._dropped: int = 0
        self._dequeued: int = 0

    def _record_enqueue(self, accepted: bool) -> None:
        if accepted:
            self._enqueued += 1
        else:
            self._dropped += 1

    def _record_dequeue(self) -> None:
        self._dequeued += 1

    @property
    def stats(self) -> dict:
        total = self._enqueued + self._dropped
        drop_rate = self._dropped / total if total else 0.0
        return {
            "enqueued": self._enqueued,
            "dropped":  self._dropped,
            "dequeued": self._dequeued,
            "drop_rate": round(drop_rate, 4),
        }

    def reset_stats(self) -> None:
        self._enqueued = self._dropped = self._dequeued = 0