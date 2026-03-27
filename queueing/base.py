# filename: queueing/base.py

"""
The File Defines the QueueDiscipline Base Class and Helpers
This file contains the blueprint for all queueing disciplines, including result tracking and statistics.
"""



class QueueDiscipline:
    """
    Base class for all queue types (FIFO, PQ, etc.).
    Subclasses must override the marked methods.
    """

    def __init__(self, capacity: int):
        if capacity == 0:
            raise ValueError("Capacity must be >= 1 (or -1 for unbounded).")
        self.max_capacity:int = capacity
        self.stats = QueueStats()

    def enqueue(self, packet) -> bool:
        """Attempt to add packet. Returns True/False or EnqueueResult."""
        raise NotImplementedError("Subclasses must implement enqueue()")
        
    
    def dequeue(self):
        """Remove and return the next packet. Returns None if empty."""
        raise NotImplementedError("Subclasses must implement dequeue()")

    def is_full(self) -> bool:
        """Return True if the queue is full."""
        raise NotImplementedError("Subclasses must implement is_full()")

    def length(self) -> int:
        """Return the current number of packets."""
        raise NotImplementedError("Subclasses must implement length()")
    
    def is_empty(self) -> bool:
        """Return True when there are no packets waiting."""
        return self.length() == 0
    
    def capacity(self) -> int:
        return self.max_capacity
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(max={self.max_capacity}, count={self.length()})"


class EnqueueResult:
    """
    Used when the metrics collector needs to record WHY a packet was dropped.
    """
    __slots__ = ("accepted", "reason")

    REASONS = {"tail_drop", "red_drop", "token_exhausted", "admitted"}

    def __init__(self, accepted: bool, reason: str = "admitted"):
        if reason not in self.REASONS:
            raise ValueError(f"Unknown drop reason '{reason}'")
        self.accepted = accepted
        self.reason = reason

    def __bool__(self):
        return self.accepted

    def __repr__(self) -> str:
        return f"EnqueueResult(accepted={self.accepted}, reason='{self.reason}')"



class QueueStats:
    def __init__(self):
        self.enqueued = 0
        self.dropped = 0
        self.dequeued = 0

    def record_enqueue(self, accepted: bool):
        if accepted:
            self.enqueued += 1
        else:
            self.dropped += 1

    def record_dequeue(self):
        self.dequeued += 1

    def get_summary(self) -> dict:
        total = self.enqueued + self.dropped
        drop_rate = self.dropped / total if total > 0 else 0.0
        return {
            "enqueued": self.enqueued,
            "dropped":  self.dropped,
            "dequeued": self.dequeued,
            "drop_rate": round(drop_rate, 4),
        }