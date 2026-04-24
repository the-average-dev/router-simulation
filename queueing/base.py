# filename: queueing/base.py

"""
This File Defines the Base Class for Queue Disciplines
Every queue discipline must implement enqueue, dequeue, is_full, and length.
router.py only ever calls these four methods.
"""


class QueueDiscipline:

    def __init__(self, capacity: int) -> None:
        if capacity == 0:
            raise ValueError("capacity must be >= 1 (or -1 for unbounded).")
        self._capacity: int = capacity

    def enqueue(self, packet) -> bool:
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement enqueue(packet)"
        )

    def dequeue(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement dequeue()"
        )

    def is_full(self) -> bool:
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement is_full()"
        )

    def length(self) -> int:
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement length()"
        )

    def is_empty(self) -> bool:
        return self.length() == 0

    @property
    def capacity(self) -> int:
        return self._capacity

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"capacity={self._capacity}, "
            f"occupancy={self.length()})"
        )


class StatsTrackingMixin:

    def __init__(self, *args, **kwargs) -> None:
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
            "enqueued":  self._enqueued,
            "dropped":   self._dropped,
            "dequeued":  self._dequeued,
            "drop_rate": round(drop_rate, 4),
        }

    def reset_stats(self) -> None:
        self._enqueued = self._dropped = self._dequeued = 0