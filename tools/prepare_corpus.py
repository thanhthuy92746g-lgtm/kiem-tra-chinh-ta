"""Prepare disjoint Wikipedia/OPUS training and evaluation texts, offline.

Held-out articles/lines are read before training is emitted. All training sources
exclude the same normalized held-out token sequences, including duplicate subtitles.
"""
import argparse
import bz2
import gzip
import hashlib
import html
import itertools
import json
import random
import re
import sys
import time
from pathlib import Path
from xml.etree import ElementTree as ET

from vietspell.core.normalize import nfc
from vietspell.core.tokenizer import sentences, tokenize


def clean_wiki(text):
    text = re.sub(r"<!--.*?-->|<(?:ref|math|score|gallery|syntaxhighlight)\b[^>]*>.*?</(?:ref|math|score|gallery|syntaxhighlight)\s*>", " ", text, flags=re.S | re.I)
    text = re.sub(r"\{\|.*?\|\}", " ", text, flags=re.S)
    for _ in range(30):
        changed = re.sub(r"\{\{[^{}]*\}\}", " ", text)
        if changed == text:
            break
        text = changed
    text = re.sub(r"\[\[(?:Tập tin|Hình|File|Image|Thể loại|Category):[^\n]*", " ", text, flags=re.I)
    for _ in range(10):
        changed = re.sub(r"\[\[(?:[^\[\]|]*\|)?([^\[\]]+)\]\]", r"\1", text)
        if changed == text:
            break
        text = changed
    text = re.sub(r"\[https?://\S+\s+([^\]]+)\]", r"\1", text)
    text = re.sub(r"https?://\S+|<[^>]+>", " ", text)
    text = re.sub(r"(?im)^\s*=+\s*(?:Tham khảo|Chú thích|Liên kết ngoài|Xem thêm)\b[\s\S]*", "", text)
    text = re.sub(r"(?m)^\s*[=*#;:|!]+", "", text)
    return nfc(html.unescape(text.replace("'''", "").replace("''", "")))


def wiki_articles(path):
    with bz2.open(path, "rb") as source:
        iterator = ET.iterparse(source, events=("start", "end"))
        _, root = next(iterator)
        for event, page in iterator:
            if event != "end" or page.tag.rsplit("}", 1)[-1] != "page":
                continue
            title = page.findtext("{*}title") or ""
            namespace = page.findtext("{*}ns")
            raw = page.findtext("{*}revision/{*}text") or ""
            if namespace == "0" and page.find("{*}redirect") is None and not re.match(r"\s*#(?:redirect|đổi)\b", raw, re.I):
                cleaned = clean_wiki(raw)
                if len(tokenize(cleaned)) >= 20:
                    yield title, cleaned
            page.clear()
            root.remove(page)


def text_sentences(text):
    text = nfc(text)
    for group in sentences(text):
        if 1 <= len(group) <= 100:
            value = text[group[0].start:group[-1].end].strip()
            # Remaining wiki syntax is not training prose.
            if any(c in value for c in "{}[]|="):
                continue
            ending = re.match(r"[)\]\"”’']*\s*[.!?…][)\]\"”’']*", text[group[-1].end:])
            yield value + (ending.group().strip() if ending else ".")


def subtitle_sentences(path):
    with gzip.open(path, "rt", encoding="utf-8-sig") as source:
        for line in source:
            line = nfc(html.unescape(re.sub(r"<[^>]*>|\{[^}]*\}", " ", line)))
            if re.search(r"https?://|www\.|dịch phụ đề|biên dịch|subscene|opensubtitles", line, re.I):
                continue
            yield from text_sentences(line)


def sentence_key(text):
    return hashlib.sha256(" ".join(t.lower for t in tokenize(text)).encode("utf-8")).digest()


def prepare(wiki_path, subtitle_path, output, max_articles=80000, heldout_count=300, progress=None):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    names = ("wiki-train.txt", "opus-train.txt", "wiki-heldout.txt", "opus-heldout.txt", "manifest.json")
    if any((output / name).exists() for name in names):
        raise FileExistsError("Thư mục đầu ra đã có dữ liệu; chọn thư mục mới để bảo vệ lần chuẩn bị trước.")
    rng = random.Random(92746)
    wiki = wiki_articles(wiki_path)
    subtitles = subtitle_sentences(subtitle_path)
    heldout = {"wiki": [], "opus": []}
    keys = set()
    titles = []
    for title, text in wiki:
        eligible = [s for s in text_sentences(text) if 6 <= len(tokenize(s)) <= 40]
        rng.shuffle(eligible)
        selected = 0
        for s in eligible:
            key = sentence_key(s)
            if key in keys:
                continue
            keys.add(key)
            heldout["wiki"].append(s)
            selected += 1
            if selected == 3 or len(heldout["wiki"]) >= heldout_count:
                break
        if selected:
            titles.append(title)
        if len(heldout["wiki"]) >= heldout_count:
            break
    for s in subtitles:
        key = sentence_key(s)
        if 6 <= len(tokenize(s)) <= 40 and key not in keys:
            keys.add(key)
            heldout["opus"].append(s)
            if len(heldout["opus"]) >= heldout_count:
                break
    if any(len(values) != heldout_count for values in heldout.values()):
        raise ValueError("Nguồn dữ liệu không đủ câu giữ riêng.")
    for name, values in heldout.items():
        (output / f"{name}-heldout.txt").write_text("\n".join(values)+"\n", encoding="utf-8")
    counts = {"wiki_articles": 0, "wiki_sentences": 0, "opus_sentences": 0, "excluded_duplicates": 0}

    def emit(file, values, key_name):
        for s in values:
            if sentence_key(s) in keys:
                counts["excluded_duplicates"] += 1
                continue
            file.write(s+"\n")
            counts[key_name] += 1

    with (output / "wiki-train.txt").open("w", encoding="utf-8") as file:
        for title, text in itertools.islice(wiki, max_articles):
            emit(file, text_sentences(text), "wiki_sentences")
            counts["wiki_articles"] += 1
            if progress and counts["wiki_articles"] % 2000 == 0:
                progress(dict(counts))
    with (output / "opus-train.txt").open("w", encoding="utf-8") as file:
        for s in subtitles:
            emit(file, (s,), "opus_sentences")
            if progress and counts["opus_sentences"] and counts["opus_sentences"] % 500000 == 0:
                progress(dict(counts))
    manifest = {"seed": 92746, "split": "Wikipedia: whole held-out articles first; OPUS: held-out prefix, then all remaining lines. Exact normalized held-out sentences excluded across both sources.",
                "heldout_counts": {k: len(v) for k, v in heldout.items()}, "heldout_wiki_titles": titles,
                "training": counts, "sources": [str(wiki_path), str(subtitle_path)],
                "limitations": "Deterministic prefix holdout, not a random representative survey. MediaWiki cleanup uses bounded regexes, not a complete renderer."}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--wiki", required=True)
    p.add_argument("--subtitles", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--max-articles", type=int, default=80000)
    p.add_argument("--heldout", type=int, default=300)
    a = p.parse_args()
    if a.max_articles < 1 or a.heldout < 1:
        p.error("Số bài và số câu giữ riêng phải từ 1 trở lên.")
    began = time.monotonic()
    def report(counts):
        print(json.dumps({"elapsed_s": round(time.monotonic()-began), **counts}), file=sys.stderr, flush=True)
    print(json.dumps(prepare(a.wiki, a.subtitles, a.out, a.max_articles, a.heldout, report), ensure_ascii=False, indent=2))
