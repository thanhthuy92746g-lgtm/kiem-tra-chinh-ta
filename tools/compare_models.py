"""Compare models on one frozen set of texts and artificial errors.

Every model sees exactly the same cases. Unreviewed source findings are not
labelled false positives. This never promotes/replaces the installed model.
"""
import argparse
import hashlib
import json
import random
import time
from collections import Counter
from pathlib import Path

from evaluate import LANGUAGE_KINDS, mutations
from prepare_corpus import sentence_key
from vietspell.core.detector import Checker
from vietspell.core.ngram import NgramModel
from vietspell.core.tokenizer import tokenize


def freeze_cases(rows, lexicon, seed=92746):
    rng = random.Random(seed)
    frozen = []
    for row in rows:
        text = row["text"]
        cases = []
        for kind in ("dialect", "typo", "diacritic"):
            choices = [(t, form) for t in tokenize(text) if t.lower in lexicon and not t.text.isupper()
                       for form in mutations(t, kind)]
            if choices:
                token, form = rng.choice(choices)
                cases.append({"kind": kind, "text": text[:token.start]+form+text[token.end:],
                              "start": token.start, "end": token.start+len(form), "gold": token.lower})
        frozen.append({**row, "cases": cases})
    return frozen


def measure(checker, frozen):
    began = time.monotonic()
    counts = {kind: {"cases": 0, "detected": 0, "top1": 0, "top5": 0} for kind in ("dialect", "typo", "diacritic")}
    marked, token_count, marked_tokens, clean_reviewed, reviewed_marked = 0, 0, 0, 0, 0
    rules, examples = Counter(), []
    for row in frozen:
        findings = [i for i in checker.check(row["text"]).issues if i.kind in LANGUAGE_KINDS]
        tokens = tokenize(row["text"])
        token_count += len(tokens)
        marked += bool(findings)
        marked_tokens += sum(any(i.start < t.end and t.start < i.end for i in findings) for t in tokens)
        rules.update(i.rule_id for i in findings)
        if row.get("review_status") == "reviewed_clean":
            clean_reviewed += 1
            reviewed_marked += bool(findings)
        if findings and len(examples) < 15:
            examples.append({"text": row["text"], "source_url": row.get("source_url"), "findings": [i.to_dict() for i in findings]})
        for case in row["cases"]:
            metric = counts[case["kind"]]
            metric["cases"] += 1
            overlap = [i for i in checker.check(case["text"]).issues if i.kind in LANGUAGE_KINDS
                       and i.start < case["end"] and case["start"] < i.end]
            metric["detected"] += bool(overlap)
            metric["top1"] += any(i.suggestions and i.suggestions[0].text.lower() == case["gold"] for i in overlap)
            metric["top5"] += any(s.text.lower() == case["gold"] for i in overlap for s in i.suggestions[:5])
    for metric in counts.values():
        n = metric["cases"]
        metric.update({key+"_rate": metric[key]/n if n else None for key in ("detected", "top1", "top5")})
    return {"sentences": len(frozen), "source_sentences_with_findings": marked,
            "source_sentence_finding_rate": marked/len(frozen) if frozen else None,
            "source_tokens": token_count, "source_tokens_with_findings": marked_tokens,
            "reviewed_clean_sentences": clean_reviewed, "reviewed_clean_with_findings": reviewed_marked,
            "reviewed_false_positive_sentence_rate": reviewed_marked/clean_reviewed if clean_reviewed else None,
            "synthetic_corruptions": counts, "source_findings_by_rule": dict(rules), "examples": examples,
            "elapsed_s": round(time.monotonic()-began, 3)}


def exclude_overlap(rows, training_paths):
    keys = {sentence_key(row["text"]) for row in rows}
    overlap = set()
    for path in training_paths:
        with Path(path).open(encoding="utf-8") as source:
            for line in source:
                key = sentence_key(line)
                if key in keys:
                    overlap.add(key)
    return [row for row in rows if sentence_key(row["text"]) not in overlap], len(overlap)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--baseline", default="data")
    p.add_argument("--candidate", action="append", required=True)
    p.add_argument("--baseline-train", action="append", default=[])
    p.add_argument("--out", required=True)
    p.add_argument("--seed", type=int, default=92746)
    a = p.parse_args()
    path = Path(a.input)
    if path.suffix == ".jsonl":
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if any(row.get("source_url") for row in rows) and not a.baseline_train:
            p.error("Đánh giá báo chí mới cần --baseline-train để kiểm tra câu trùng nguồn train cũ.")
    else:
        rows = [{"text": line.strip(), "review_status": "unreviewed_source"} for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    rows, removed = exclude_overlap(rows, a.baseline_train) if a.baseline_train else (rows, 0)
    if not rows:
        p.error("Không còn câu đánh giá độc lập.")
    output = Path(a.out)
    output.mkdir(parents=True, exist_ok=False)
    with NgramModel(Path(a.baseline)/"ngram.sqlite") as reference:
        if reference.meta.get("quality") != "corpus":
            p.error("Mô hình tham chiếu phải là corpus.")
        frozen = freeze_cases(rows, reference.lexicon, a.seed)
    dataset = json.dumps(frozen, ensure_ascii=False, sort_keys=True).encode("utf-8")
    (output/"fixed-cases.json").write_bytes(dataset)
    report = {"seed": a.seed, "dataset_sha256": hashlib.sha256(dataset).hexdigest(), "training_overlap_removed": removed,
              "note": "Fixed cases shared by every model. Artificial errors; source findings are not confirmed false positives unless reviewed_clean. Existing wiki/OPUS holdouts were used in earlier checker development.", "models": []}
    for folder in [a.baseline]+a.candidate:
        db = Path(folder)/"ngram.sqlite"
        print("Đo mô hình:", folder, flush=True)
        with NgramModel(db) as model:
            if model.meta.get("quality") != "corpus":
                raise ValueError("Không so chất lượng bằng mô hình mẫu.")
            result = measure(Checker(model), frozen)
            result.update({"path": folder, "model_sha256": hashlib.sha256(db.read_bytes()).hexdigest(), "meta": model.meta})
        report["models"].append(result)
        (output/"comparison.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(output/"comparison.json"), "dataset_sha256": report["dataset_sha256"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
