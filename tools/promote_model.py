"""Install a candidate model only after product regressions and integrity checks."""
import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path

from validate_model import validate
from vietspell.core.ngram import NgramModel
from vietspell.paths import data_dir


def promote(candidate, destination):
    candidate, destination = Path(candidate).resolve(), Path(destination).resolve()
    if candidate == destination:
        raise ValueError("Mô hình ứng viên và đích phải ở hai thư mục khác nhau.")
    report = validate(candidate / "ngram.sqlite")
    if not report["passed"]:
        raise ValueError("Ứng viên chưa qua đủ các ca hồi quy; giữ nguyên mô hình đang dùng.")
    with NgramModel(candidate / "ngram.sqlite") as model:
        if model.db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("SQLite không qua kiểm tra toàn vẹn.")
        if set((candidate / "syllables.txt").read_text(encoding="utf-8").splitlines()) != model.lexicon:
            raise ValueError("Từ điển âm tiết không khớp cơ sở dữ liệu.")
    for name in ("evaluation-wiki.json", "evaluation-opus.json", "evaluation-wiki-strict.json", "evaluation-opus-strict.json"):
        if (candidate / name).is_file():
            evaluation = json.loads((candidate / name).read_text(encoding="utf-8"))
            if evaluation.get("model_sha256") != report["model_sha256"]:
                raise ValueError("Báo cáo đánh giá không thuộc mô hình ứng viên hiện tại; hãy đánh giá lại.")
    destination.mkdir(parents=True, exist_ok=True)
    backup_root = destination / "backups"
    backup_root.mkdir(exist_ok=True)
    backup = Path(tempfile.mkdtemp(prefix="model-", dir=backup_root))
    artifacts = ("ngram.sqlite", "syllables.txt", "MODEL-CARD.md", "model-provenance.json", "model-validation.json", "evaluation-wiki.json", "evaluation-opus.json", "evaluation-wiki-strict.json", "evaluation-opus-strict.json")
    for name in artifacts:
        if (destination / name).exists():
            shutil.copy2(destination / name, backup / name)
    for name in artifacts:
        source = candidate / name
        if not source.is_file():
            continue
        fd, temporary = tempfile.mkstemp(prefix=".model-", dir=destination)
        os.close(fd)
        try:
            shutil.copy2(source, temporary)
            os.replace(temporary, destination / name)
        finally:
            Path(temporary).unlink(missing_ok=True)
    (destination / "model-validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if not (destination / "whitelist.txt").exists():
        (destination / "whitelist.txt").write_text("# Mỗi dòng một từ được miễn soát.\n", encoding="utf-8")
    return {"backup": str(backup), "model_sha256": report["model_sha256"], "checks_passed": report["checks"]}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Đóng GUI trước khi thay mô hình; giữ lại bản sao mô hình cũ và whitelist.")
    p.add_argument("--candidate", required=True)
    p.add_argument("--data", default=str(data_dir()))
    a = p.parse_args()
    print(json.dumps(promote(a.candidate, a.data), ensure_ascii=False, indent=2))
