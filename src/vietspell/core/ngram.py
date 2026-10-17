import math
import sqlite3
from functools import lru_cache
from pathlib import Path

BIGRAM_WEIGHT = 0.75
TRIGRAM_WEIGHT = 0.65


class NgramModel:
    """Connections belong to the thread that opens them. Never share with a Qt worker."""

    def __init__(self, path: str | Path):
        self.path = Path(path).resolve()
        self.db = sqlite3.connect(self.path.as_uri() + "?mode=ro", uri=True)
        self.db.execute("PRAGMA query_only=ON")
        self.meta = dict(self.db.execute("SELECT key, value FROM meta"))
        self.total = int(self.meta["total_syllables"])
        self.lexicon = frozenset(w for (w,) in self.db.execute("SELECT syllable FROM unigram"))
        self.vocab = len(self.lexicon)
        if not self.total or not self.vocab:
            self.close()
            raise ValueError("Mô hình không có dữ liệu; hãy huấn luyện lại.")
        # Instance caches avoid retaining old models after a check finishes.
        for name in ("c1", "c2", "c3", "p1", "p2", "p3"):
            setattr(self, name, lru_cache(maxsize=50000)(getattr(self, name)))

    def c1(self, w):
        row = self.db.execute("SELECT count FROM unigram WHERE syllable=?", (w,)).fetchone()
        return row[0] if row else 0

    def c2(self, a, b):
        row = self.db.execute("SELECT count FROM bigram WHERE w1=? AND w2=?", (a, b)).fetchone()
        return row[0] if row else 0

    def c3(self, a, b, c):
        row = self.db.execute("SELECT count FROM trigram WHERE w1=? AND w2=? AND w3=?", (a, b, c)).fetchone()
        return row[0] if row else 0

    def p1(self, w):
        return (self.c1(w) + 0.5) / (self.total + 0.5 * self.vocab)

    def p2(self, a, b):
        count = self.c1(a)
        return BIGRAM_WEIGHT * self.c2(a, b) / count + (1-BIGRAM_WEIGHT) * self.p1(b) if count else self.p1(b)

    def p3(self, a, b, c):
        count = self.c2(a, b)
        return TRIGRAM_WEIGHT * self.c3(a, b, c) / count + (1-TRIGRAM_WEIGHT) * self.p2(b, c) if count else self.p2(b, c)

    def logprob(self, context, word):
        p = self.p3(*context[-2:], word) if len(context) >= 2 else self.p2(context[-1], word) if context else self.p1(word)
        return math.log10(max(p, 1e-300))

    def close(self):
        self.db.close()
        for name in ("c1", "c2", "c3", "p1", "p2", "p3"):
            method = getattr(self, name)
            if hasattr(method, "cache_clear"):
                method.cache_clear()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
