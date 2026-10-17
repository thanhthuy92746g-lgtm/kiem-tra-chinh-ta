from copy import deepcopy
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from .reader import paragraph_runs, read_docx


class ExportMode(str, Enum):
    RED = "RED"
    TRACK = "TRACK"
    PLAIN = "PLAIN"
    HIGHLIGHT = "HIGHLIGHT"


def text_run(template, text, *, deleted=False, red=False, highlight=False):
    run = OxmlElement("w:r")
    if template.rPr is not None:
        run.append(deepcopy(template.rPr))
    if red or highlight:
        properties = run.get_or_add_rPr()
        tag = "w:color" if red else "w:highlight"
        for old in list(properties.findall(qn(tag))):
            properties.remove(old)
        prop = OxmlElement(tag)
        prop.set(qn("w:val"), "FF0000" if red else "yellow")
        properties.append(prop)
    # Preserve tabs and hard breaks in sliced text.
    chunks = text.replace("\t", "\x00\t\x00").replace("\n", "\x00\n\x00").split("\x00")
    for chunk in chunks:
        if not chunk:
            continue
        node = OxmlElement("w:tab" if chunk == "\t" else "w:br" if chunk == "\n" else "w:delText" if deleted else "w:t")
        if chunk not in {"\t", "\n"}:
            node.text = chunk
            node.set(qn("xml:space"), "preserve")
        run.append(node)
    return run


def export_docx(source: bytes, output, edits, mode=ExportMode.RED):
    """edits: (Issue, replacement) pairs. Source bytes remain unchanged."""
    mode = ExportMode(mode)
    read = read_docx(source)
    selected = sorted(edits, key=lambda pair: pair[0].start)
    previous_end = -1
    for issue, replacement in selected:
        if not (0 <= issue.start < issue.end <= len(read.text)) or read.text[issue.start:issue.end] != issue.text:
            raise ValueError("Vị trí sửa không khớp tài liệu đang mở; hãy soát lại tệp.")
        if issue.start < previous_end:
            raise ValueError("Có các chỗ sửa chồng lấn; hãy chọn lại.")
        previous_end = issue.end
        if not any(b.start <= issue.start and issue.end <= b.end for b in read.blocks):
            raise ValueError("Không tự thay chữ xuyên qua ranh giới đoạn; hãy sửa dòng trống trong Word.")
    ids = [int(e.get(qn("w:id"))) for tag in ("w:ins", "w:del") for e in read.document.element.iter(qn(tag)) if (e.get(qn("w:id")) or "").isdigit()]
    revision_id = max(ids, default=0)+1
    for issue, replacement in reversed(selected):
        block = next(b for b in read.blocks if b.start <= issue.start and issue.end <= b.end)
        local_start, local_end = issue.start-block.start, issue.end-block.start
        start = block.mapping[local_start][0]
        end = block.mapping[local_end-1][1]
        spans = [s for s in paragraph_runs(block.paragraph) if s.start < end and start < s.end]
        if not spans:
            raise ValueError("Không tìm được run để sửa.")
        allowed = {qn(t) for t in ("w:rPr", "w:t", "w:tab", "w:br", "w:cr", "w:lastRenderedPageBreak", "w:noBreakHyphen")}
        for span in spans:
            if any(child.tag not in allowed for child in span.run._r):
                raise ValueError("Chỗ sửa chứa trường hoặc đối tượng Word; hãy sửa trực tiếp trong Word.")
            if any(a.tag in {qn("w:ins"), qn("w:del")} for a in span.run._r.iterancestors()):
                raise ValueError("Chỗ sửa thuộc thay đổi cũ; hãy chấp nhận/từ chối thay đổi trong Word trước.")
        first, last = spans[0], spans[-1]
        anchor = first.run._r
        parent = anchor.getparent()
        insertion_index = parent.index(anchor)
        nodes = []
        prefix = first.text[:max(0, start-first.start)]
        suffix = last.text[end-last.start:]
        if prefix:
            nodes.append(text_run(anchor, prefix))
        if mode == ExportMode.TRACK:
            old_parts = [s.text[max(0, start-s.start):min(len(s.text), end-s.start)] for s in spans]
            deletion = OxmlElement("w:del")
            insertion = OxmlElement("w:ins")
            for node in (deletion, insertion):
                node.set(qn("w:id"), str(revision_id))
                revision_id += 1
                node.set(qn("w:author"), "VietSpell")
                node.set(qn("w:date"), datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
            for span, old in zip(spans, old_parts):
                deletion.append(text_run(span.run._r, old, deleted=True))
            nodes.append(deletion)
            if replacement:
                insertion.append(text_run(anchor, replacement))
                nodes.append(insertion)
        elif mode == ExportMode.HIGHLIGHT:
            for span in spans:
                chunk = span.text[max(0, start-span.start):min(len(span.text), end-span.start)]
                nodes.append(text_run(span.run._r, chunk, highlight=True))
        elif replacement:
            nodes.append(text_run(anchor, replacement, red=mode == ExportMode.RED))
        # Last suffix must stay in its original hyperlink/container and keep its formatting.
        suffix_node = text_run(last.run._r, suffix) if suffix else None
        last_parent = last.run._r.getparent()
        if suffix_node is not None:
            last.run._r.addnext(suffix_node)
        for node in nodes:
            parent.insert(insertion_index, node)
            insertion_index += 1
        for span in spans:
            span.run._r.getparent().remove(span.run._r)
    if mode == ExportMode.TRACK:
        settings = read.document.settings.element
        if settings.find(qn("w:trackRevisions")) is None:
            settings.append(OxmlElement("w:trackRevisions"))
    output = Path(output)
    # A partial write never replaces an existing output on an exception.
    import tempfile
    import os
    fd, temp = tempfile.mkstemp(prefix=".vietspell-", suffix=".docx", dir=output.parent)
    os.close(fd)
    try:
        read.document.save(temp)
        os.replace(temp, output)
    finally:
        Path(temp).unlink(missing_ok=True)
    return output
