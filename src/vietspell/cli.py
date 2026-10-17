import argparse
import json
import sys

from .core.detector import Checker
from .core.legal import PROFILES
from .core.ngram import NgramModel
from .paths import data_dir
from .service import DocumentSession


def configure_stdio():
    for stream in (sys.stdout, sys.stderr):
        if stream is not None and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def _safe_print(text, **kwargs):
    stream = kwargs.pop("file", sys.stdout)
    if stream is not None:
        try:
            print(text, file=stream, **kwargs)
        except UnicodeEncodeError:
            print(str(text).encode(stream.encoding or "utf-8", errors="replace").decode(stream.encoding or "utf-8"), file=stream, **kwargs)


def main(argv=None):
    configure_stdio()
    p = argparse.ArgumentParser(description="VietSpell — soát Word hoàn toàn ngoại tuyến")
    p.add_argument("--data", default=str(data_dir()), help="Thư mục chứa ngram.sqlite và whitelist.txt")
    commands = p.add_subparsers(dest="command")
    commands.add_parser("gui")
    commands.add_parser("doctor")
    for name in ("check", "fix"):
        sub = commands.add_parser(name)
        sub.add_argument("file", nargs="?")
        sub.add_argument("--text", help="Soát văn bản thuần thay vì tệp; chỉ dùng với check")
        sub.add_argument("--profile", choices=PROFILES, default="HC-ND30")
        sub.add_argument("--report", help="Xuất báo cáo JSON")
        if name == "fix":
            sub.add_argument("-o", "--output", required=True)
            sub.add_argument("--mode", choices=("RED", "TRACK", "PLAIN", "HIGHLIGHT"), default="RED")
    a = p.parse_args(argv)
    try:
        if a.command in {None, "gui"}:
            from .gui.app import run
            return run(a.data)
        from pathlib import Path
        if a.command == "doctor":
            with NgramModel(Path(a.data) / "ngram.sqlite") as model:
                integrity = model.db.execute("PRAGMA quick_check").fetchone()[0]
                if integrity != "ok":
                    raise ValueError("SQLite: "+integrity)
                _safe_print(json.dumps({"python": sys.version.split()[0], "sqlite": integrity, "lexicon": model.vocab, "model": model.meta}, ensure_ascii=False, indent=2))
            return 0
        if a.text is not None:
            if a.command != "check":
                p.error("--text chỉ dùng với check; fix cần một tệp .docx.")
            with NgramModel(Path(a.data) / "ngram.sqlite") as model:
                result = Checker(model, profile=a.profile).check(a.text)
                if model.meta.get("quality") == "demo":
                    result.warnings.append("Mô hình mẫu: chưa đo chất lượng trên văn bản thực tế.")
            payload = json.dumps(result.to_dict(), ensure_ascii=False, indent=2)
            _safe_print(payload)
            if a.report:
                Path(a.report).write_text(payload, encoding="utf-8")
        else:
            if not a.file:
                p.error("Cần đường dẫn .docx hoặc --text.")
            session = DocumentSession(a.file, a.data)
            result = session.check(a.profile)
            _safe_print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
            if a.command == "fix":
                session.export(a.output, mode=a.mode)
                _safe_print(f"Đã xuất {a.output}; các lỗi định dạng cần sửa trực tiếp trong Word.")
            if a.report:
                session.report(a.report)
        # check: 0 clean, 1 findings, 2 operational failure. fix: 0 exported.
        return 1 if a.command == "check" and result.issues else 0
    except Exception as exc:
        _safe_print(f"Không thực hiện được: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
