"""Prepare/restore the reviewed corpus model for the Windows CI runner.

Only curated model artifacts are included. The user's whitelist, raw corpus,
input documents and local directories are never copied into the CI bundle.
"""
import argparse
import hashlib
import json
import os
import shutil
import tempfile
import zipfile
from pathlib import Path

MODEL_SHA256 = "52847125dd6f51d79fe956b19ea3150ee1abb3a634201198c8afcb7e47e121d8"
MODEL_FILES = (
    "ngram.sqlite", "syllables.txt", "MODEL-CARD.md", "model-provenance.json",
    "model-validation.json", "evaluation-wiki.json", "evaluation-opus.json",
    "evaluation-wiki-strict.json", "evaluation-opus-strict.json",
)
WHITELIST = b"# One exempt word per line. No personal whitelist bundled for CI.\n"


def sha256(path):
    with Path(path).open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def validate_model(folder):
    from vietspell.core.ngram import NgramModel
    if sha256(folder / "ngram.sqlite") != MODEL_SHA256:
        raise ValueError("Mô hình không khớp SHA-256 đã kiểm chứng.")
    report = json.loads((folder / "model-validation.json").read_text(encoding="utf-8"))
    if not report["passed"] or report["model_sha256"] != MODEL_SHA256:
        raise ValueError("Thiếu báo cáo hồi quy đạt cho mô hình này.")
    with NgramModel(folder / "ngram.sqlite") as model:
        if model.meta.get("quality") != "corpus" or model.vocab != 7880:
            raise ValueError("Cần đúng mô hình ngữ liệu thật đã kiểm chứng.")
        if model.db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise ValueError("SQLite không qua quick_check.")
        if set((folder / "syllables.txt").read_text(encoding="utf-8").splitlines()) != model.lexicon:
            raise ValueError("Từ điển âm tiết không khớp SQLite.")


def prepare(folder, archive):
    folder, archive = Path(folder).resolve(), Path(archive).resolve()
    validate_model(folder)
    archive.parent.mkdir(parents=True, exist_ok=True)
    manifest = {name: sha256(folder / name) for name in MODEL_FILES}
    manifest["whitelist.txt"] = hashlib.sha256(WHITELIST).hexdigest()
    fd, temporary = tempfile.mkstemp(prefix=".ci-model-", suffix=".zip", dir=archive.parent)
    os.close(fd)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as output:
            for name in MODEL_FILES:
                output.write(folder / name, name)
            output.writestr("whitelist.txt", WHITELIST)
            output.writestr("SHA256SUMS.json", json.dumps(manifest, sort_keys=True, indent=2))
        os.replace(temporary, archive)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return {"path": str(archive), "bytes": archive.stat().st_size, "sha256": sha256(archive),
            "model_sha256": MODEL_SHA256, "contains_personal_whitelist": False}


def restore(archive, folder):
    archive, folder = Path(archive).resolve(), Path(folder).resolve()
    if folder.exists() and any(folder.iterdir()):
        raise ValueError("Thư mục đích đã có dữ liệu; không ghi đè mô hình hoặc whitelist đang dùng.")
    folder.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".ci-model-", dir=folder.parent))
    try:
        with zipfile.ZipFile(archive) as source:
            expected = set(MODEL_FILES) | {"whitelist.txt", "SHA256SUMS.json"}
            if set(source.namelist()) != expected or len(source.namelist()) != len(expected):
                raise ValueError("ZIP có thành phần khác danh sách mô hình cho phép.")
            manifest = json.loads(source.read("SHA256SUMS.json"))
            if set(manifest) != expected-{"SHA256SUMS.json"}:
                raise ValueError("Manifest mô hình không đầy đủ.")
            for name in manifest:
                content = source.read(name)
                if hashlib.sha256(content).hexdigest() != manifest[name]:
                    raise ValueError("Tệp không khớp checksum: "+name)
                (temporary / name).write_bytes(content)
        if (temporary / "whitelist.txt").read_bytes() != WHITELIST:
            raise ValueError("Gói CI không được chứa whitelist cá nhân.")
        validate_model(temporary)
        if folder.exists():
            folder.rmdir()  # Empty was verified above; rmdir fails if it changed.
        temporary.rename(folder)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return {"model_sha256": MODEL_SHA256, "destination": str(folder), "passed": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "restore"))
    parser.add_argument("--data", default="data")
    parser.add_argument("--archive", default="resources/trained-model.zip")
    args = parser.parse_args()
    result = prepare(args.data, args.archive) if args.action == "prepare" else restore(args.archive, args.data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
