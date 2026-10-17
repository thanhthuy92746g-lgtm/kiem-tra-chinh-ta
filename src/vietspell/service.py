import json
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .core.detector import Checker, CheckerConfig
from .core.ngram import NgramModel
from .core.tokenizer import tokenize
from .core.types import CheckResult, Issue
from .docx_io.element_check import check_elements
from .docx_io.format_check import check_document_format
from .docx_io.reader import read_docx
from .docx_io.writer import ExportMode, export_docx
from .paths import data_dir


@dataclass
class CheckStats:
    paragraphs: int
    words: int
    total: int
    levels: dict
    kinds: dict
    elapsed: float


class CheckCancelled(Exception):
    pass


class DocumentSession:
    def __init__(self, path, model_dir=None):
        self.path = Path(path)
        if self.path.suffix.lower() != ".docx":
            raise ValueError("Chỉ hỗ trợ tệp Word .docx; hãy chuyển .doc sang .docx trong Word.")
        self.source = self.path.read_bytes()
        self.read = read_docx(self.source)
        self.model_dir = Path(model_dir) if model_dir else data_dir()
        self.result = None
        self.stats = None

    def check(self, profile="HC-ND30", config=None, progress=None, cancelled=None):
        started = time.perf_counter()
        issues = []
        warnings = list(self.read.warnings)
        element_issues, elements = check_elements(self.read, profile)
        subject_blocks = {id(e.block) for e in elements if e.role in {"subject", "letter_subject"}}
        with NgramModel(self.model_dir / "ngram.sqlite") as model:
            if model.meta.get("quality") == "demo":
                warnings.insert(0, "Đang dùng mô hình MẪU nhỏ: chỉ để thử chức năng; chưa đạt chất lượng soát văn bản thực tế.")
            whitelist_path = self.model_dir / "whitelist.txt"
            whitelist = [line.strip() for line in whitelist_path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")] if whitelist_path.exists() else []
            checker = Checker(model, config, whitelist, profile)
            total = len(self.read.blocks)
            for count, b in enumerate(self.read.blocks, 1):
                if cancelled and cancelled():
                    raise CheckCancelled()
                result = checker.check(b.text)
                for issue in result.issues:
                    # A subject is a phrase, not a new sentence. HD05's own
                    # examples start with lower-case “về việc”, “kết quả”…
                    if issue.rule_id == "LOWERCASE_SENTENCE_START" and id(b) in subject_blocks:
                        continue
                    issue.start += b.start
                    issue.end += b.start
                    issues.append(issue)
                if progress:
                    progress(count, total)
            issues += element_issues
            issues += check_document_format(self.read, profile, [e.block for e in elements if e.role == "body"])
        # Textual findings within a canonical header correction should be presented once.
        canonical = [i for i in issues if i.rule_id.startswith("ELEMENT_TEXT_")]
        issues = [i for i in issues if i in canonical or not (i.editable and any(c.start <= i.start < c.end for c in canonical))]
        issues.sort(key=lambda i: (i.start, i.end, i.rule_id))
        self.result = CheckResult(self.read.text, issues, warnings)
        self.stats = CheckStats(len(self.read.blocks), len(tokenize(self.read.text)), len(issues), dict(Counter(i.severity for i in issues)), dict(Counter(i.kind for i in issues)), time.perf_counter()-started)
        return self.result

    def export(self, output, selections=None, mode=ExportMode.RED):
        if self.result is None:
            raise ValueError("Hãy soát lỗi trước khi xuất tệp.")
        output = Path(output)
        if output.resolve() == self.path.resolve():
            raise ValueError("Hãy chọn tên tệp khác để giữ nguyên bản gốc.")
        if selections is None:
            selections = self.highlight_selections() if ExportMode(mode) == ExportMode.HIGHLIGHT else [(issue, issue.suggestions[0].text) for issue in self.result.issues if issue.editable and "\n" not in issue.text]
        return export_docx(self.source, output, selections, mode)

    def highlight_selections(self):
        if self.result is None:
            raise ValueError("Hãy soát lỗi trước khi tô sáng.")
        selections = []
        for block in self.read.blocks:
            spans = sorted((max(block.start, i.start), min(block.end, i.end)) for i in self.result.issues if i.start < block.end and block.start < i.end)
            merged = []
            for start, end in spans:
                if merged and start <= merged[-1][1]:
                    merged[-1] = (merged[-1][0], max(merged[-1][1], end))
                else:
                    merged.append((start, end))
            for start, end in merged:
                value = self.read.text[start:end]
                selections.append((Issue(start, end, value, "Tô sáng", "HIGHLIGHT"), value))
        return selections

    def report(self, output):
        if self.result is None:
            raise ValueError("Hãy soát lỗi trước khi xuất báo cáo.")
        if Path(output).resolve() == self.path.resolve():
            raise ValueError("Không ghi đè tài liệu gốc bằng báo cáo; hãy chọn tên .json khác.")
        from dataclasses import asdict
        payload = {"file": self.path.name, "stats": asdict(self.stats), **self.result.to_dict()}
        Path(output).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
