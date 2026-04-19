from __future__ import annotations

import abc
from typing import Any, Optional

PacketLike = Any   


class QueueDiscipline(abc.ABC):
    

    def __init__(self, capacity: int) -> None:
        if capacity == 0:
            raise ValueError("capacity must be ≥ 1 (or -1 for unbounded).")
        self._capacity: int = capacity

    
    
    

    @abc.abstractmethod
    def enqueue(self, packet: PacketLike) -> bool:
        """
        Attempt to add a packet to the queue.
        Parameters
        packet : PacketLike
            The packet to be enqueued.

        Returns

        bool
            True if the packet was accepted, False if it was dropped.
        """

    @abc.abstractmethod
    def dequeue(self) -> Optional[PacketLike]:
        """
        Remove and return the next packet from the queue.
        Returns
        Optional[PacketLike]
            The next packet in the queue, or None if the queue is empty.
        """

    @abc.abstractmethod
    def is_full(self) -> bool:
        """
        Return True if the queue cannot accept any more packets right now.
        """

    def is_empty(self) -> bool:
        return self.__len__() == 0

    @property
    def capacity(self) -> int:
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






class EnqueueResult:
    

    __slots__ = ("accepted", "reason")

    REASONS = frozenset({
        "tail_drop",       
        "red_drop",        
        "token_exhausted", 
        "admitted",        
    })

    def __init__(self, accepted: bool, reason: str = "admitted") -> None:
        if reason not in self.REASONS:
            raise ValueError(f"Unknown drop reason '{reason}'. Valid: {self.REASONS}")
        self.accepted: bool = accepted
        self.reason: str = reason

    def __bool__(self) -> bool:          
        return self.accepted

    def __repr__(self) -> str:
        return f"EnqueueResult(accepted={self.accepted}, reason={self.reason!r})"






class StatsTrackingMixin:
    

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
