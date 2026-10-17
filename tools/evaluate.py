"""Reproducible evaluation on supplied held-out sentences, never on demo data."""
import argparse
import hashlib
import json
import random
import sys
import time
from collections import Counter

from vietspell.core.confusion import PREFIX_GROUPS
from vietspell.core.detector import Checker, CheckerConfig
from vietspell.core.ngram import NgramModel
from vietspell.core.normalize import fold_diacritics, match_case, nfc
from vietspell.core.tokenizer import sentences, tokenize
from vietspell.paths import data_dir
from vietspell.training import corpus_lines

LANGUAGE_KINDS = {"unknown", "context", "confusion", "fuzzy", "diacritic", "abbrev"}


def mutations(token, kind):
    word = token.lower
    if kind == "diacritic":
        folded = fold_diacritics(word)
        return [match_case(token.text, folded)] if folded != word else []
    if kind == "typo":
        return [token.text[:i]+token.text[i+1:] for i in range(1, len(word)-1)] if len(word) >= 4 else []
    choices = []
    for group in PREFIX_GROUPS:
        for prefix in group:
            if word.startswith(prefix):
                choices += [match_case(token.text, other+word[len(prefix):]) for other in group if other != prefix]
    return choices


def evaluate(checker, texts, seed=92746, progress=None):
    rng = random.Random(seed)
    false_sentences = 0
    false_tokens = 0
    total_tokens = 0
    examples = []
    clean_rules = Counter()
    metrics = {kind: {"cases": 0, "detected": 0, "top1": 0, "top5": 0} for kind in ("dialect", "typo", "diacritic")}
    for ordinal, text in enumerate(texts, 1):
        tokens = tokenize(text)
        total_tokens += len(tokens)
        clean = [i for i in checker.check(text).issues if i.kind in LANGUAGE_KINDS]
        false_sentences += bool(clean)
        clean_rules.update(i.rule_id for i in clean)
        if clean and len(examples) < 20:
            examples.append({"text": text, "findings": [i.to_dict() for i in clean]})
        false_tokens += len({index for index, token in enumerate(tokens) if any(i.start < token.end and token.start < i.end for i in clean)})
        for kind, result in metrics.items():
            options = [(t, form) for t in tokens if t.lower in checker.model.lexicon and not t.text.isupper() for form in mutations(t, kind)]
            if not options:
                continue
            token, mutated = rng.choice(options)
            corrupted = text[:token.start]+mutated+text[token.end:]
            result["cases"] += 1
            findings = [i for i in checker.check(corrupted).issues if i.kind in LANGUAGE_KINDS and i.start < token.start+len(mutated) and token.start < i.end]
            result["detected"] += bool(findings)
            candidates = [s.text.lower() for i in findings for s in i.suggestions[:5]]
            result["top1"] += any(i.suggestions and i.suggestions[0].text.lower() == token.lower for i in findings)
            result["top5"] += token.lower in candidates
        if progress and ordinal % 10 == 0:
            progress(ordinal, len(texts))
    for result in metrics.values():
        n = result["cases"]
        result.update({name+"_rate": result[name]/n if n else None for name in ("detected", "top1", "top5")})
    return {"sentences": len(texts), "syllables": total_tokens,
            "false_positive_sentences": false_sentences, "false_positive_syllables": false_tokens,
            "false_positive_sentence_rate": false_sentences/len(texts) if texts else None,
            "false_positive_syllable_rate": false_tokens/total_tokens if total_tokens else None,
            "synthetic_corruptions": metrics, "clean_sentence_findings_examples": examples,
            "clean_findings_by_rule": dict(clean_rules),
            "note": "Mỗi loại: tối đa một lỗi nhân tạo/câu đủ điều kiện; không phải thước đo độ chính xác trên lỗi tự nhiên."}


def main():
    p = argparse.ArgumentParser(description="Đánh giá trên ngữ liệu giữ riêng, chưa dùng huấn luyện.")
    p.add_argument("--input", required=True)
    p.add_argument("--data", default=str(data_dir()))
    p.add_argument("--sentences", type=int, default=300)
    p.add_argument("--min-confusion", type=float, default=2.5)
    p.add_argument("--min-fuzzy", type=float, default=4.0)
    p.add_argument("--min-diacritic", type=float, default=1.0)
    p.add_argument("--context-threshold", type=float, default=-3.0)
    p.add_argument("--seed", type=int, default=92746)
    p.add_argument("--output", help="Lưu kết quả JSON vào tệp ngoài việc in stdout")
    a = p.parse_args()
    if a.sentences < 1:
        p.error("--sentences phải từ 1 trở lên.")
    from pathlib import Path
    texts = []
    for line in corpus_lines(a.input):
        line = nfc(line)
        for group in sentences(line):
            if len(group) >= 4:
                texts.append(line[group[0].start:group[-1].end]+".")
                if len(texts) >= a.sentences:
                    break
        if len(texts) >= a.sentences:
            break
    if not texts:
        p.error("Không có câu giữ riêng đủ điều kiện đánh giá.")
    config = CheckerConfig(min_delta_confusion=a.min_confusion, min_delta_fuzzy=a.min_fuzzy,
                           min_delta_diacritic=a.min_diacritic, context_threshold=a.context_threshold)
    with NgramModel(Path(a.data) / "ngram.sqlite") as model:
        if model.meta.get("quality") == "demo":
            p.error("Không đo chất lượng với mô hình mẫu. Hãy huấn luyện bằng ngữ liệu thật trước.")
        from dataclasses import asdict
        began = time.monotonic()
        result = evaluate(Checker(model, config), texts, a.seed,
            progress=lambda n, total: print(f"Đánh giá {n}/{total} câu, {time.monotonic()-began:.1f}s", file=sys.stderr, flush=True))
        result["config"] = asdict(config)
        result["model"] = model.meta
        with model.path.open("rb") as source:
            result["model_sha256"] = hashlib.file_digest(source, "sha256").hexdigest()
        import vietspell.core.detector as detector_module
        import vietspell.core.proper_nouns as proper_module
        result["checker_code_sha256"] = {Path(m.__file__).name: hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest() for m in (detector_module, proper_module)}
        result["evaluation_use"] = "Held out from language-model training; also used to diagnose checker rules, so these are development measurements, not a blind final test."
        payload = json.dumps(result, ensure_ascii=False, indent=2)
        if a.output:
            Path(a.output).write_text(payload, encoding="utf-8")
        print(payload)


if __name__ == "__main__":
    main()
