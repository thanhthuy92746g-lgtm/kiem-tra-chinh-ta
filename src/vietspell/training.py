"""Explicit development-time training; never imported by the checking pipeline."""
import bz2
import gzip
import json
import re
import sqlite3
import time
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

from .core.normalize import nfc
from .core.syllable import generate_syllables
from .core.tokenizer import sentences

SCHEMA = """
CREATE TABLE unigram(syllable TEXT PRIMARY KEY, count INTEGER NOT NULL) WITHOUT ROWID;
CREATE TABLE bigram(w1 TEXT, w2 TEXT, count INTEGER NOT NULL, PRIMARY KEY(w1,w2)) WITHOUT ROWID;
CREATE TABLE trigram(w1 TEXT, w2 TEXT, w3 TEXT, count INTEGER NOT NULL, PRIMARY KEY(w1,w2,w3)) WITHOUT ROWID;
CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL) WITHOUT ROWID;
"""


def corpus_lines(path, max_articles=80000):
    path = Path(path)
    if path.name.endswith(".xml.bz2"):
        with bz2.open(path, "rb") as source:
            articles = 0
            for event, elem in ET.iterparse(source, events=("end",)):
                if elem.tag.endswith("}text"):
                    text = elem.text or ""
                    text = re.sub(r"\{\{[^{}]*\}\}|<[^>]*>|\[\[File:[^\]]*\]\]", " ", text)
                    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", text)
                    yield text
                    articles += 1
                    if max_articles and articles >= max_articles:
                        break
                if elem.tag.endswith("}page"):
                    elem.clear()
    else:
        opener = gzip.open if path.suffix == ".gz" else open
        with opener(path, "rt", encoding="utf-8-sig") as source:
            yield from source


def build_model(lines, output, *, sources, quality="corpus", min_unigram=4, min_bigram=4, min_trigram=5, prune_every=150000, progress=None):
    """Aggregate bounded batches into disk tables, prune only at finalization.

    Discarding low counts on every batch would silently lose globally frequent
    ngrams. prune_every is the flush interval, not destructive interim pruning.
    """
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    staging = output / "_ngram-staging.sqlite"
    if staging.exists():
        raise FileExistsError(f"Còn tệp huấn luyện trước: {staging}; đổi --out hoặc kiểm tra rồi xoá tệp tạm này.")
    db = sqlite3.connect(staging)
    db.execute("PRAGMA cache_size=-131072")  # 128 MiB; bound memory for large corpora.
    db.executescript(SCHEMA)
    valid = generate_syllables()
    counts = [Counter(), Counter(), Counter()]
    total, sentence_count = 0, 0
    began = time.monotonic()

    def flush():
        for n, table in enumerate(("unigram", "bigram", "trigram"), 1):
            columns = "syllable" if n == 1 else ",".join(f"w{i}" for i in range(1, n+1))
            placeholders = ",".join("?" for _ in range(n+1))
            db.executemany(f"INSERT INTO {table} VALUES ({placeholders}) ON CONFLICT({columns}) DO UPDATE SET count=count+excluded.count", ((*key, count) for key, count in counts[n-1].items()))
            counts[n-1].clear()
        db.commit()
        if progress:
            progress({"sentences": sentence_count, "syllables": total, "elapsed_s": round(time.monotonic()-began), "staging_mib": round(staging.stat().st_size/1024**2, 1)})

    try:
        for line in lines:
            for tokens in sentences(nfc(line)):
                # Unknown/foreign words break context instead of joining unrelated neighbours.
                sequence = [t.lower for t in tokens]
                for i, word in enumerate(sequence):
                    if word not in valid:
                        continue
                    counts[0][(word,)] += 1
                    total += 1
                    if i and sequence[i-1] in valid:
                        counts[1][tuple(sequence[i-1:i+1])] += 1
                    if i >= 2 and all(w in valid for w in sequence[i-2:i]):
                        counts[2][tuple(sequence[i-2:i+1])] += 1
                sentence_count += 1
                if sentence_count % (prune_every or 150000) == 0:
                    flush()
        flush()
        db.execute("DELETE FROM unigram WHERE count < ?", (min_unigram,))
        for table, threshold, columns in (("bigram", min_bigram, ("w1", "w2")), ("trigram", min_trigram, ("w1", "w2", "w3"))):
            db.execute(f"DELETE FROM {table} WHERE count < ?", (threshold,))
            for column in columns:
                db.execute(f"DELETE FROM {table} WHERE {column} NOT IN (SELECT syllable FROM unigram)")
        lexicon = [w for (w,) in db.execute("SELECT syllable FROM unigram ORDER BY syllable")]
        if not lexicon:
            raise ValueError("Ngữ liệu không có âm tiết hợp lệ hoặc ngưỡng đếm quá cao.")
        retained_total = db.execute("SELECT SUM(count) FROM unigram").fetchone()[0]
        meta = {"total_syllables": str(retained_total), "observed_syllables": str(total), "lexicon_size": str(len(lexicon)), "sentences": str(sentence_count), "sources": json.dumps(sources, ensure_ascii=False), "quality": quality, "schema_version": "1", "trainer_version": "2", "syllable_generator_version": "2",
                "min_unigram": str(min_unigram), "min_bigram": str(min_bigram), "min_trigram": str(min_trigram)}
        db.executemany("INSERT INTO meta VALUES (?,?)", meta.items())
        db.commit()
        db.execute("VACUUM")
    finally:
        db.close()
    staging.replace(output / "ngram.sqlite")
    (output / "syllables.txt").write_text("\n".join(lexicon)+"\n", encoding="utf-8")
    whitelist = output / "whitelist.txt"
    if not whitelist.exists():
        whitelist.write_text("# Mỗi dòng một từ được miễn soát; không phân biệt hoa thường.\n", encoding="utf-8")
    return meta
