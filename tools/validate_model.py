"""Run product regressions against the actual installed/candidate language model."""
import argparse
import hashlib
import json
import time
from pathlib import Path

from vietspell.core.detector import Checker
from vietspell.core.format_rules import FormatChecker
from vietspell.core.ngram import NgramModel
from vietspell.paths import data_dir

REQUIRED = [
    ("Hôm nay bạn an gì. Tôi đang di chơi.", [("an", "ăn"), (".", "?"), ("di", "đi")]),
    ("Tôi đang di chơi.", [("di", "đi")]),
    ("Co biết sửa cai nay ko?", [("Co", "Có"), ("cai", "cái"), ("nay", "này"), ("ko", "không")]),
    ("toi di hoc o truong", [("toi", "Tôi"), ("di", "đi"), ("hoc", "học"), ("o", "ở"), ("truong", "trường")]),
    ("Trong công tác, Nhất là công tác giải phóng mặt bằng.", [("Nhất", "nhất")]),
    ("An ninh minh tế.", [("minh", "kinh")]),
    ("Tôi sẽ sử lý hồ sơ.", [("sử", "xử")]),
]
CLEAN = ["Công trình cống Đôi đã hoàn thành.", "Ban chỉ đạo", "Công an tỉnh",
         "Độc lập – Tự do – Hạnh phúc", "- Như trên;", "Tôi không biết gì cả.",
         "Tôi đang đi chơi.", "UBND CAT-ANKT Đ/c V/v", "VietSpell iPhone macOS"]


def validate(model_path):
    began = time.monotonic()
    outcomes = []
    with NgramModel(model_path) as model:
        checker = Checker(model)
        for text, expected in REQUIRED:
            issues = checker.check(text).issues
            actual = [(i.text, i.suggestions[0].text) for i in issues if i.editable]
            outcomes.append({"text": text, "expected": expected, "actual": actual,
                             "passed": actual == expected, "findings": [i.to_dict() for i in issues]})
        for text in CLEAN:
            issues = checker.check(text).issues
            outcomes.append({"text": text, "passed": not issues, "findings": [i.to_dict() for i in issues]})
        outcomes.append({"text": "Xin  chào các bạn   .", "passed": FormatChecker().fix("Xin  chào các bạn   .") == "Xin chào các bạn."})
        meta = dict(model.meta)
    with Path(model_path).open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    return {"passed": all(row["passed"] for row in outcomes), "checks": len(outcomes),
            "elapsed_s": round(time.monotonic()-began, 3), "model": meta,
            "model_sha256": digest,
            "outcomes": outcomes}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data", default=str(data_dir()))
    p.add_argument("--output")
    a = p.parse_args()
    report = validate(Path(a.data) / "ngram.sqlite")
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if a.output:
        Path(a.output).write_text(payload, encoding="utf-8")
    print(payload)
    raise SystemExit(0 if report["passed"] else 1)
