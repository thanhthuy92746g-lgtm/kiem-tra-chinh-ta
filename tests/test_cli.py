import importlib.util
import json
from pathlib import Path

from docx import Document

from vietspell.cli import main
from vietspell.docx_io.reader import read_docx
from vietspell.core.detector import Checker


def test_cli_doctor_and_check_outcome(model_dir, capsys):
    assert main(["--data", str(model_dir), "doctor"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["sqlite"] == "ok" and payload["lexicon"] > 0
    assert main(["--data", str(model_dir), "check", "--text", "Hôm nay bạn an gì. Tôi đang di chơi."]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert len(payload["issues"]) == 3
    assert main(["--data", str(model_dir), "check", "--text", "Tôi đang đi chơi."]) == 0


def test_cli_missing_model_fails(model_dir, capsys):
    assert main(["--data", str(model_dir / "missing"), "doctor"]) == 2
    assert "Không thực hiện được" in capsys.readouterr().err


def test_cli_word_export_and_report(tmp_path, model_dir, capsys):
    source, out, report = (tmp_path / n for n in ("source.docx", "fixed.docx", "report.json"))
    document = Document()
    document.add_paragraph("Tôi đang di chơi.")
    document.save(source)
    original = source.read_bytes()
    assert main(["--data", str(model_dir), "fix", str(source), "-o", str(out), "--mode", "TRACK", "--report", str(report)]) == 0
    assert read_docx(out).text == "Tôi đang đi chơi."
    assert source.read_bytes() == original
    assert json.loads(report.read_text(encoding="utf-8"))["file"] == "source.docx"
    assert main(["--data", str(model_dir), "check", str(source), "--report", str(source)]) == 2
    assert source.read_bytes() == original


def test_evaluator_counts_executed_cases(model):
    path = Path(__file__).resolve().parents[1] / "tools/evaluate.py"
    spec = importlib.util.spec_from_file_location("vietspell_evaluate_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    texts = ["Tôi đang đi chơi.", "Hôm nay bạn ăn gì.", "Công an tỉnh triển khai kế hoạch."]
    report = module.evaluate(Checker(model), texts, seed=1)
    assert report["sentences"] == 3
    assert report["syllables"] == 16
    for outcome in report["synthetic_corruptions"].values():
        assert 0 < outcome["cases"] <= 3
        assert 0 <= outcome["detected"] <= outcome["cases"]
        assert 0 <= outcome["top1"] <= outcome["top5"] <= outcome["cases"]
