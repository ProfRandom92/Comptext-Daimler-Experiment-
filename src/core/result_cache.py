"""
LRU-Cache für Analyseergebnisse.

Cache-Key: MD5-Checksum des KVTC-Frames (KVTCResult.checksum).
Gleicher Dokumentinhalt → gleicher Frame → gleiche Checksum → Cache-Hit.

Thread-sicher via threading.Lock für FastAPI-Multithread-Betrieb.
"""

from __future__ import annotations

import threading
from collections import OrderedDict
from dataclasses import dataclass

from src.models.schemas import Analyseergebnis


@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0
    evictions: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class AnalysisResultCache:
    """
    Thread-sicherer LRU-Cache für Analyseergebnisse.

    LRU-Eviction: move_to_end(key) on hit, popitem(last=False) on overflow.
    Kein externes Package benötigt – reine stdlib-Implementierung.
    """

    def __init__(self, max_size: int = 256) -> None:
        self._max_size = max_size
        self._cache: OrderedDict[str, Analyseergebnis] = OrderedDict()
        self._lock = threading.Lock()
        self.stats = CacheStats()

    def get(self, checksum: str) -> Analyseergebnis | None:
        with self._lock:
            if checksum in self._cache:
                self._cache.move_to_end(checksum)
                self.stats.hits += 1
                return self._cache[checksum]
            self.stats.misses += 1
            return None

    def put(self, checksum: str, result: Analyseergebnis) -> None:
        with self._lock:
            if checksum in self._cache:
                self._cache.move_to_end(checksum)
            self._cache[checksum] = result
            if len(self._cache) > self._max_size:
                self._cache.popitem(last=False)
                self.stats.evictions += 1

    def invalidate(self, checksum: str) -> bool:
        with self._lock:
            return self._cache.pop(checksum, None) is not None

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    @property
    def size(self) -> int:
        return len(self._cache)
