"""Make a source + trained-model handoff without corpus, venv, or build caches."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path


def make_bundle(destination):
    root = Path(__file__).resolve().parents[1]
    files = []
    for directory in (".github", "docs", "packaging", "resources", "src", "tests", "tools"):
        files.extend(p for p in (root / directory).rglob("*") if p.is_file() and not p.is_symlink()
                     and "__pycache__" not in p.parts and p.suffix not in {".pyc", ".pyo"}
                     and p != root / "resources/trained-model.zip")
    files.extend(root / name for name in (".gitignore", "LICENSE.txt", "README.md", "THIRD-PARTY-NOTICES.md", "pyproject.toml", "requirements-dev.lock"))
    for name in ("ngram.sqlite", "syllables.txt", "whitelist.txt", "MODEL-CARD.md", "model-provenance.json", "model-validation.json", "evaluation-wiki.json", "evaluation-opus.json", "evaluation-wiki-strict.json", "evaluation-opus-strict.json"):
        path = root / "data" / name
        if not path.is_file():
            raise ValueError("Thiếu tệp bàn giao: "+str(path.relative_to(root)))
        files.append(path)
    for directory in ("release-check", "release-frozen-linux"):
        folder = root / "data" / directory
        report = json.loads((folder / "release-report.json").read_text(encoding="utf-8"))
        if not report["passed"]:
            raise ValueError("Chưa đạt kiểm tra: "+directory)
        files.extend(p for p in folder.iterdir() if p.is_file() and p.suffix in {".json", ".docx"})
    files = sorted(set(files))
    manifest = {str(p.relative_to(root)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    if manifest["data/ngram.sqlite"] != "52847125dd6f51d79fe956b19ea3150ee1abb3a634201198c8afcb7e47e121d8":
        raise ValueError("Mô hình đã đổi; phải đánh giá lại và cập nhật manifest trước khi bàn giao.")
    destination = Path(destination).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in files:
            archive.write(path, "VietSpell/"+str(path.relative_to(root)).replace("\\", "/"))
        archive.writestr("VietSpell/SHA256SUMS.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    with zipfile.ZipFile(destination) as archive:
        if archive.testzip():
            raise ValueError("ZIP lỗi CRC.")
    print(json.dumps({"path": str(destination), "files": len(files)+1, "bytes": destination.stat().st_size,
                      "sha256": hashlib.sha256(destination.read_bytes()).hexdigest()}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    make_bundle(parser.parse_args().output)
