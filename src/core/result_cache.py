"""
LRU-Cache für Analyseergebnisse mit optionalem TTL.

Cache-Key: MD5-Checksum des KVTC-Frames (KVTCResult.checksum).
Gleicher Dokumentinhalt → gleicher Frame → gleiche Checksum → Cache-Hit.

Thread-sicher via threading.Lock für FastAPI-Multithread-Betrieb.
"""

from __future__ import annotations

import time
import threading
from collections import OrderedDict
from dataclasses import dataclass

from src.models.schemas import Analyseergebnis


@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expirations: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class AnalysisResultCache:
    """
    Thread-sicherer LRU-Cache mit TTL für Analyseergebnisse.

    LRU-Eviction: move_to_end(key) on hit, popitem(last=False) on overflow.
    TTL-Eviction: einträge älter als ttl_seconds werden bei Zugriff verworfen.
    ttl_seconds=0 deaktiviert TTL-Prüfung.
    """

    def __init__(self, max_size: int = 256, ttl_seconds: int = 3600) -> None:
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._cache: OrderedDict[str, Analyseergebnis] = OrderedDict()
        self._timestamps: dict[str, float] = {}
        self._lock = threading.Lock()
        self.stats = CacheStats()

    def _is_expired(self, checksum: str) -> bool:
        if self._ttl <= 0:
            return False
        ts = self._timestamps.get(checksum)
        return ts is None or (time.monotonic() - ts) > self._ttl

    def get(self, checksum: str) -> Analyseergebnis | None:
        with self._lock:
            if checksum not in self._cache:
                self.stats.misses += 1
                return None
            if self._is_expired(checksum):
                del self._cache[checksum]
                del self._timestamps[checksum]
                self.stats.expirations += 1
                self.stats.misses += 1
                return None
            self._cache.move_to_end(checksum)
            self.stats.hits += 1
            return self._cache[checksum]

    def put(self, checksum: str, result: Analyseergebnis) -> None:
        with self._lock:
            if checksum in self._cache:
                self._cache.move_to_end(checksum)
            self._cache[checksum] = result
            self._timestamps[checksum] = time.monotonic()
            if len(self._cache) > self._max_size:
                oldest, _ = self._cache.popitem(last=False)
                self._timestamps.pop(oldest, None)
                self.stats.evictions += 1

    def invalidate(self, checksum: str) -> bool:
        with self._lock:
            self._timestamps.pop(checksum, None)
            return self._cache.pop(checksum, None) is not None

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()

    @property
    def size(self) -> int:
        return len(self._cache)
