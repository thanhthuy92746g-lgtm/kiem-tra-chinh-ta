from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph
from docx.text.run import Run

from ..core.normalize import index_map, nfc


@dataclass
class RunSpan:
    run: Run
    start: int
    end: int
    text: str


@dataclass
class ParagraphBlock:
    paragraph: Paragraph
    start: int
    end: int
    text: str
    raw: str
    mapping: list[tuple[int, int]]
    runs: list[RunSpan]


@dataclass
class ReadDocument:
    document: object
    text: str
    blocks: list[ParagraphBlock]
    warnings: list[str]


def iter_paragraphs(element, parent):
    """Traverse body/table/content-controls in XML order, including nested tables."""
    for child in element.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, parent)
        elif child.tag in {qn("w:tbl"), qn("w:tr"), qn("w:tc"), qn("w:sdt"), qn("w:sdtContent"), qn("w:customXml")}:
            yield from iter_paragraphs(child, parent)


def visible_runs(paragraph):
    for r in paragraph._p.iter(qn("w:r")):
        ancestors = list(r.iterancestors())
        if any(a.tag in {qn("w:del"), qn("w:txbxContent")} for a in ancestors):
            continue
        # Do not include a nested textbox's paragraph in its outer paragraph.
        if next((a for a in ancestors if a.tag == qn("w:p")), None) is paragraph._p:
            yield Run(r, paragraph)


def run_text(run):
    result = []
    for node in run._r:
        if node.tag == qn("w:t"):
            result.append(node.text or "")
        elif node.tag == qn("w:tab"):
            result.append("\t")
        elif node.tag in {qn("w:br"), qn("w:cr")}:
            result.append("\n")
        elif node.tag == qn("w:noBreakHyphen"):
            result.append("‑")
    return "".join(result)


def paragraph_runs(paragraph):
    spans, cursor = [], 0
    for run in visible_runs(paragraph):
        text = run_text(run)
        spans.append(RunSpan(run, cursor, cursor+len(text), text))
        cursor += len(text)
    return spans


def paragraph_leading_tab(paragraph):
    text = "".join(s.text for s in paragraph_runs(paragraph))
    return text.lstrip(" ").startswith("\t")


def read_docx(source: str | Path | bytes):
    document = Document(BytesIO(source) if isinstance(source, bytes) else source)
    blocks, cursor, texts = [], 0, []
    for paragraph in iter_paragraphs(document.element.body, document):
        runs = paragraph_runs(paragraph)
        raw = "".join(s.text for s in runs)
        text = nfc(raw)
        blocks.append(ParagraphBlock(paragraph, cursor, cursor+len(text), text, raw, index_map(raw), runs))
        texts.append(text)
        cursor += len(text)+1
    warnings = []
    if any(True for _ in document.element.body.iter(qn("w:txbxContent"))):
        warnings.append("Nội dung trong hộp văn bản chưa được soát; hãy kiểm tra trong Word.")
    if any(True for _ in document.element.body.iter(qn("w:ins"))) or any(True for _ in document.element.body.iter(qn("w:del"))):
        warnings.append("Tệp đã có theo dõi thay đổi: soát phần đang hiển thị, bỏ qua phần đã xoá; không sửa tự động bên trong thay đổi cũ.")
    warnings.append("Phạm vi soát: phần thân và bảng; đầu/chân trang, chú thích và hộp văn bản cần kiểm tra trong Word.")
    return ReadDocument(document, "\n".join(texts), blocks, warnings)
