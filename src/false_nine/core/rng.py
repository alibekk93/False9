from __future__ import annotations

import hashlib
import random


class Rng:
    """Seeded randomness with named substreams.

    Streams are derived by hashing `(seed, name, key)`, so adding a call site in one
    system never shifts results in another. Deriving with blake2b rather than the
    builtin `hash()` is load-bearing: `hash()` is salted per process by PYTHONHASHSEED,
    which would break reproducibility across runs and void every stored save.
    """

    def __init__(self, seed: str) -> None:
        self.seed = seed
        self._streams: dict[tuple[str, str], random.Random] = {}

    def stream(self, name: str, key: object = "") -> random.Random:
        cache_key = (name, str(key))
        stream = self._streams.get(cache_key)
        if stream is None:
            # Cached, so repeated calls within one stream advance instead of repeating.
            digest = hashlib.blake2b(
                f"{self.seed}|{name}|{cache_key[1]}".encode(), digest_size=8
            ).digest()
            stream = random.Random(int.from_bytes(digest, "big"))
            self._streams[cache_key] = stream
        return stream
