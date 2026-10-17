from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from lxml import etree

from ..core.legal import BASIS_EDITORIAL, PROFILES
from ..core.types import Issue
from .reader import paragraph_leading_tab


def style_chain(style):
    seen = set()
    while style is not None and style.style_id not in seen:
        seen.add(style.style_id)
        yield style
        style = style.base_style


def inherited_font(run, attribute, document):
    candidates = [run.font]
    if run.style is not None:
        candidates += [s.font for s in style_chain(run.style)]
    candidates += [s.font for s in style_chain(run._parent.style)]
    candidates += [document.styles["Normal"].font]
    for font in candidates:
        value = getattr(font, attribute)
        if value is not None:
            return value
    defaults = document.styles.element.find(qn("w:docDefaults"))
    rpr = defaults.find(qn("w:rPrDefault")) if defaults is not None else None
    rpr = rpr.find(qn("w:rPr")) if rpr is not None else None
    if rpr is not None and attribute in {"bold", "italic"}:
        node = rpr.find(qn("w:b" if attribute == "bold" else "w:i"))
        if node is not None:
            return node.get(qn("w:val"), "1") not in {"false", "0", "off"}
    if rpr is not None and attribute == "size":
        node = rpr.find(qn("w:sz"))
        if node is not None:
            from docx.shared import Pt
            return Pt(int(node.get(qn("w:val")))/2)
    return None


def effective_font_name(run, document):
    """Resolve concrete and theme font names in the same inheritance order."""
    properties = [run._r.rPr]
    properties += [s.element.rPr for s in style_chain(run.style)]
    properties += [s.element.rPr for s in style_chain(run._parent.style)]
    properties += [document.styles["Normal"].element.rPr]
    defaults = document.styles.element.find(qn("w:docDefaults"))
    if defaults is not None:
        default = defaults.find(qn("w:rPrDefault"))
        if default is not None:
            properties.append(default.find(qn("w:rPr")))
    for prop in properties:
        fonts = prop.find(qn("w:rFonts")) if prop is not None else None
        if fonts is None:
            continue
        for script in ("ascii", "hAnsi"):
            theme_key = fonts.get(qn("w:"+script+"Theme"))
            if theme_key:
                group = "majorFont" if theme_key.startswith("major") else "minorFont"
                for relation in document.part.rels.values():
                    if relation.reltype.endswith("/theme"):
                        tree = etree.fromstring(relation.target_part.blob)
                        ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
                        found = tree.find(f".//a:fontScheme/a:{group}/a:latin", ns)
                        if found is not None:
                            return found.get("typeface")
            explicit = fonts.get(qn("w:"+script))
            if explicit:
                return explicit
    return None


def paragraph_setting(paragraph, name):
    for fmt in [paragraph.paragraph_format] + [s.paragraph_format for s in style_chain(paragraph.style)]:
        value = getattr(fmt, name)
        if value is not None:
            return value
    return None


def check_document_format(read, profile="HC-ND30", body_blocks=None):
    p = PROFILES[profile]
    issues = []

    def add(block, rule, message, basis=None):
        issues.append(Issue(block.start if block else 0, block.end if block else 0,
                            block.text if block else "", message, rule, "document", "medium",
                            basis=basis or p.basis+(", Mục I và II." if profile == "HC-ND30" else ", Phần II, IV; I.6.2.2.")))

    for index, section in enumerate(read.document.sections, 1):
        width, height = sorted((section.page_width.mm, section.page_height.mm))
        if abs(width-210) > 1 or abs(height-297) > 1:
            add(None, "PAGE_SIZE", f"Phần {index}: khổ giấy cần là A4 (210 × 297 mm).")
        if section.page_width > section.page_height:
            add(None, "PAGE_ORIENTATION", f"Phần {index}: kiểm tra trang ngang; chỉ phù hợp một số phụ lục, bảng biểu.")
        for label, name, (lo, hi) in zip(("trên", "dưới", "trái", "phải"), ("top_margin", "bottom_margin", "left_margin", "right_margin"), p.margins):
            value = getattr(section, name).mm
            if not lo-0.1 <= value <= hi+0.1:
                add(None, "PAGE_MARGIN_"+name.upper(), f"Phần {index}: lề {label} {value:.1f} mm; hồ sơ yêu cầu {lo}–{hi} mm.")
    bodies = body_blocks if body_blocks is not None else [b for b in read.blocks if len(b.text) > 80]
    last_body = bodies[-1] if bodies else None
    for b in read.blocks:
        for span in b.runs:
            if not span.text.strip():
                continue
            name = effective_font_name(span.run, read.document)
            if name and name.casefold() != "times new roman":
                add(b, "FONT_NAME", f"Phông chữ “{name}”; hồ sơ yêu cầu Times New Roman.")
                break
        for node in b.paragraph._p.iter(qn("w:br")):
            if node.get(qn("w:type"), "textWrapping") == "textWrapping":
                add(b, "SOFT_BREAK", "Có Shift+Enter; kiểm tra có cần tách thành đoạn mới không.", BASIS_EDITORIAL)
                break
        # Word's lastRenderedPageBreak is deliberately ignored.
    for b in bodies:
        paragraph = b.paragraph
        align = paragraph_setting(paragraph, "alignment")
        if align == WD_ALIGN_PARAGRAPH.CENTER:
            continue
        indent = paragraph_setting(paragraph, "first_line_indent")
        max_indent = 12.7 if profile == "HC-ND30" else 10
        if not paragraph_leading_tab(paragraph) and not (indent and 10-0.2 <= indent.mm <= max_indent+0.2):
            message = "Nội dung nên lùi đầu dòng 1–1,27 cm; tab đầu dòng cũng được chấp nhận." if profile == "HC-ND30" else "Nội dung HD05 lùi đầu dòng khoảng 10 mm; kiểm tra cả vị trí dừng tab nếu dùng tab."
            add(b, "FIRST_LINE_INDENT", message)
        if align not in {WD_ALIGN_PARAGRAPH.JUSTIFY, WD_ALIGN_PARAGRAPH.DISTRIBUTE}:
            add(b, "BODY_ALIGNMENT", "Nội dung nên căn đều hai lề.")
        after = paragraph_setting(paragraph, "space_after")
        next_body = bodies[bodies.index(b)+1] if b is not last_body else None
        before_next = paragraph_setting(next_body.paragraph, "space_before") if next_body is not None else None
        if b is not last_body and max(after.pt if after else 0, before_next.pt if before_next else 0) < 6:
            add(b, "SPACE_AFTER", "Khoảng cách giữa các đoạn nội dung cần tối thiểu 6 pt (Before/After).")
        spacing = paragraph_setting(paragraph, "line_spacing")
        rule = paragraph_setting(paragraph, "line_spacing_rule")
        if profile == "HC-ND30":
            if isinstance(spacing, float) and not 1 <= spacing <= 1.5:
                add(b, "LINE_SPACING", "Giãn dòng nội dung cần trong khoảng đơn đến 1,5 dòng.")
        elif rule != WD_LINE_SPACING.EXACTLY or spacing is None or not 18 <= getattr(spacing, "pt", 0) <= 22:
            add(b, "LINE_SPACING", "Hồ sơ HD05 dùng giãn dòng Exactly 18–22 pt.")
        for span in b.runs:
            if not span.text.strip():
                continue
            size = inherited_font(span.run, "size", read.document)
            if size is not None and not p.body_size[0] <= size.pt <= p.body_size[1]:
                add(b, "BODY_SIZE", f"Cỡ chữ nội dung {size.pt:g}; yêu cầu {p.body_size[0]}–{p.body_size[1]} pt.")
                break
        for span in b.runs:
            color = span.run.font.color
            if color.rgb is not None and str(color.rgb) != "000000":
                add(b, "BODY_COLOR", "Nội dung có màu chữ khác đen; kiểm tra định dạng.")
                break
    return merge_repeats(issues)


def merge_repeats(issues):
    grouped = {}
    for issue in issues:
        key = (issue.rule_id, issue.message)
        if key not in grouped:
            grouped[key] = issue
        else:
            old = grouped[key]
            old.start, old.end = min(old.start, issue.start), max(old.end, issue.end)
            old.occurrences += 1
    for issue in grouped.values():
        if issue.occurrences > 1:
            issue.message += f" (lặp lại ở {issue.occurrences} chỗ)"
    return list(grouped.values())
