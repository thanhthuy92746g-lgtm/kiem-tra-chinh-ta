import re
from dataclasses import dataclass
from difflib import SequenceMatcher

from ..core.elements import CANONICAL_TEXT, HD05_ELEMENTS, ND30_ELEMENTS
from ..core.legal import PROFILES, normalize_dashes
from ..core.normalize import fold_diacritics
from ..core.types import Issue, Suggestion
from .format_check import inherited_font, merge_repeats

NUMBER = re.compile(r"Số\s*:\s*([0-9]*)\s*/([A-ZĐ0-9/-]+)", re.I)
PARTY_NUMBER = re.compile(r"^Số\s*:?[ \t]*([0-9]*)\s*[-/]\s*([A-ZĐ0-9/-]+)")
DATE = re.compile(r"\bngày\s*(?:\d{1,2}\s*)?tháng\s*(?:\d{1,2}\s*)?năm\s*(?:\d{4})?", re.I)
DOCUMENT_TYPES = {"BÁO CÁO", "QUYẾT ĐỊNH", "THÔNG BÁO", "KẾ HOẠCH", "TỜ TRÌNH", "CHỈ THỊ", "NGHỊ QUYẾT", "HƯỚNG DẪN", "QUY CHẾ", "QUY ĐỊNH", "KẾT LUẬN", "CHƯƠNG TRÌNH", "THÔNG TRI", "THÔNG CÁO", "BIÊN BẢN", "ĐỀ ÁN"}
TYPE_CODES = {"BC", "QĐ", "QD", "TB", "KH", "TTr", "CT", "NQ", "HD", "QC", "QĐ"}


@dataclass
class IdentifiedElement:
    role: str
    block: object
    confidence: str = "high"
    text_start: int = 0
    text_end: int | None = None

    @property
    def text(self):
        return self.block.text[self.text_start:self.text_end]

    @property
    def runs(self):
        block = self.block
        end = len(block.text) if self.text_end is None else self.text_end
        if end <= self.text_start:
            return []
        raw_start = block.mapping[self.text_start][0]
        raw_end = block.mapping[end-1][1]
        return [span for span in block.runs if span.start < raw_end and raw_start < span.end
                and block.raw[max(span.start, raw_start):min(span.end, raw_end)].strip()]


class ElementIdentifier:
    def identify(self, read, profile="HC-ND30"):
        blocks = [b for b in read.blocks if b.text.strip()]
        result = []
        occupied = set()

        def add(role, block, confidence="high", start=0, end=None):
            result.append(IdentifiedElement(role, block, confidence, start, end))
            occupied.add(id(block))

        number_pattern = NUMBER if profile == "HC-ND30" else PARTY_NUMBER
        type_index = next((i for i, b in enumerate(blocks) if b.text.strip().upper() in DOCUMENT_TYPES), None)
        number_index = None
        for i, b in enumerate(blocks):
            text = b.text.strip()
            for role, canonical in CANONICAL_TEXT.items():
                folded = fold_diacritics(normalize_dashes(text)).lower()
                target = fold_diacritics(canonical).lower()
                if SequenceMatcher(None, folded, target).ratio() > 0.82:
                    add(role, b)
                    break
            if number_pattern.search(text):
                add("number", b)
                if number_index is None:
                    number_index = i
            label = re.match(r"^\s*Nơi nhận\s*:", b.text, re.I)
            if label:
                add("recipients_label", b, end=label.end())
                if b.text[label.end():].strip():
                    add("recipients", b, start=label.end())
            greeting = re.match(r"^\s*Kính (?:gửi|trình)\s*:", b.text, re.I)
            if greeting:
                add("greeting", b, end=greeting.end())
                if b.text[greeting.end():].strip():
                    add("addressees", b, start=greeting.end())
        if number_index is not None:
            # A number line is an anchor, not a reason to stop searching the header.
            for b in blocks[number_index:number_index+6]:
                if b.text.strip().upper() in DOCUMENT_TYPES:
                    break
                if DATE.search(b.text):
                    add("date", b)
                    break
            agency = [b for b in blocks[:number_index] if id(b) not in occupied and b.text.strip() and not re.fullmatch(r"[*_\-–—\s]+", b.text)]
            if agency:
                add("agency", agency[-1], "medium")
                for b in agency[:-1]:
                    add("agency_parent", b, "medium")
        else:
            for b in blocks[:10]:
                if DATE.search(b.text):
                    add("date", b)
                    break
        if profile == "DANG-HD05" and number_index is not None and type_index is None:
            number_block = blocks[number_index]
            # A party letter has no type line and no V/v prefix. Its subject may
            # span several paragraphs in the same left-hand header cell.
            started = False
            for b in blocks[number_index+1:]:
                if id(b) in occupied or b.paragraph._p.getparent() is not number_block.paragraph._p.getparent():
                    break
                text = b.text.strip()
                if not started and not re.match(r"^(?:V/v\b|về\b)", text):
                    break
                if started and (re.fullmatch(r"[*_\-–—\s]+", text) or not b.runs or not all(inherited_font(s.run, "italic", read.document) for s in b.runs if s.text.strip())):
                    break
                add("letter_subject", b, "medium")
                started = True
        for i, b in enumerate(blocks):
            if b.text.strip().upper() in DOCUMENT_TYPES:
                add("type", b, "medium")
                if i+1 < len(blocks) and id(blocks[i+1]) not in occupied:
                    add("subject", blocks[i+1], "medium")
                break
            if re.match(r"^V/v\b", b.text.strip()):
                if id(b) not in occupied:
                    add("letter_subject", b, "medium")
        # Greeting lists are distinct from the small-font Nơi nhận list.
        for i, b in enumerate(blocks):
            if any(e.role == "greeting" and e.block is b for e in result):
                for following in blocks[i+1:]:
                    if id(following) in occupied or not following.text.strip().startswith(("-", "–", "•")):
                        break
                    add("addressees", following, "medium")
        # Never search for signer's position in header agency names.
        positions = re.compile(r"\b(?:GIÁM ĐỐC|CHỦ TỊCH|TRƯỞNG|BÍ THƯ|BỘ TRƯỞNG|CỤC TRƯỞNG|HIỆU TRƯỞNG|CHÁNH VĂN PHÒNG|CHỦ NHIỆM)\b")
        recipient_index = next((blocks.index(e.block) for e in result if e.role == "recipients_label"), len(blocks))
        header_end = max((blocks.index(e.block) for e in result if e.role in {"type", "subject", "letter_subject", "date", "number", "greeting", "addressees"}), default=-1)
        body_candidates = [b for i, b in enumerate(blocks) if header_end < i < recipient_index and id(b) not in occupied
                           and not re.fullmatch(r"[*_\-–—\s]+", b.text) and not (b.text.strip().isupper() and positions.search(b.text))
                           and not re.match(r"^\s*(?:TM\.|KT\.|TL\.|TUQ\.|Q\.|T/M|K/T|T/L)\s", b.text)]
        # Use the first signature marker as the end of the body, including in
        # layouts where the signature cell precedes Nơi nhận in XML order.
        signature_index = next((i for i, b in enumerate(blocks) if i > header_end and id(b) not in occupied
                                and (re.match(r"^(?:TM\.|KT\.|TL\.|TUQ\.|Q\.|T/M|K/T|T/L)\s", b.text.strip())
                                     or b.text.strip().isupper() and positions.search(b.text))), len(blocks))
        body_candidates = [b for b in body_candidates if blocks.index(b) < signature_index]
        last_body_index = max((blocks.index(b) for b in body_candidates), default=header_end)
        for i, b in enumerate(blocks):
            text = b.text.strip()
            if i <= last_body_index or id(b) in occupied or re.match(r"^[-–•]", text) or re.search(r"\d", text):
                continue
            if re.match(r"^(?:TM\.|KT\.|TL\.|TUQ\.|Q\.|T/M|K/T|T/L)\s", text):
                add("authority", b)
                if positions.search(text):
                    # Combined authority+position has the same visual requirements.
                    pass
            elif positions.search(text) and text.isupper():
                add("position", b, "medium")
            elif i > recipient_index and text.startswith(("-", "–", "•")):
                add("recipients", b)
        for i, b in enumerate(blocks):
            if i > recipient_index and b.text.strip().startswith(("-", "–", "•")):
                add("recipients", b)
        signature_anchor = max((blocks.index(e.block) for e in result if e.role in {"position", "authority"}), default=None)
        if signature_anchor is not None:
            for b in blocks[signature_anchor+1:]:
                if id(b) not in occupied and not re.search(r"\d", b.text) and 2 <= len(b.text.split()) <= 6 and all(w[:1].isupper() for w in b.text.split()):
                    add("signer", b, "medium")
                    break
        for b in body_candidates:
            if id(b) not in occupied:
                add("body", b)
        return result


def check_elements(read, profile="HC-ND30"):
    specs = ND30_ELEMENTS if profile == "HC-ND30" else HD05_ELEMENTS
    p = PROFILES[profile]
    identified = ElementIdentifier().identify(read, profile)
    issues = []
    found = {e.role for e in identified}
    for role, spec in specs.items():
        if spec.required and role not in found:
            issues.append(Issue(0, 0, "", f"Chưa nhận diện được thành phần: {spec.title}. Hãy kiểm tra trong Word.", "MISSING_"+role.upper(), "element", "medium", basis=p.basis+", thành phần thể thức.", confidence="medium"))
    for element in identified:
        role, b, confidence = element.role, element.block, element.confidence
        if role not in specs or role == "body":
            continue
        spec = specs[role]

        def add(rule, message, suggestions=None, severe=False):
            if confidence == "medium":
                message += " (nhận diện tự động theo vị trí, độ tin cậy trung bình)"
            basis = p.basis+", Mục V." if profile == "HC-ND30" else p.basis+", Phần II, IV.2; Phụ lục 2."
            issues.append(Issue(b.start+element.text_start, b.start+(len(b.text) if element.text_end is None else element.text_end), element.text, f"{spec.title}: {message}", rule, "element", "low" if confidence == "medium" else "high" if severe else "medium", suggestions or [], basis, confidence))

        canonical = CANONICAL_TEXT.get(role)
        canonical_variants = {canonical}
        if role == "national":
            canonical_variants.add(canonical.replace("HÒA", "HOÀ"))
        fixed_text_wrong = canonical and normalize_dashes(element.text.strip()) not in canonical_variants
        if fixed_text_wrong:
            add("ELEMENT_TEXT_"+role.upper(), "nội dung hoặc cách viết hoa chưa đúng mẫu.", [Suggestion(canonical)], True)
        elif spec.uppercase and element.text.strip() != element.text.strip().upper():
            add("ELEMENT_CASE_"+role.upper(), "cần viết hoa toàn bộ.", [Suggestion(element.text.upper())])
        for attribute in ("bold", "italic", "underline", "size"):
            if attribute != "size" and getattr(spec, attribute) is None:
                continue
            bad = False
            for span in element.runs:
                if not span.text.strip():
                    continue
                value = inherited_font(span.run, attribute, read.document)
                if attribute == "size":
                    bad = value is not None and not spec.sizes[0] <= value.pt <= spec.sizes[1]
                else:
                    bad = bool(value) != getattr(spec, attribute)
                if bad:
                    break
            if bad:
                descriptions = {"bold": "cần in đậm" if spec.bold else "cần chữ đứng, không đậm", "italic": "cần in nghiêng" if spec.italic else "không dùng chữ nghiêng", "underline": "cần gạch chân", "size": f"cỡ chữ cần {spec.sizes[0]}–{spec.sizes[1]} pt"}
                add("ELEMENT_"+attribute.upper()+"_"+role.upper(), descriptions[attribute]+"; sửa định dạng trực tiếp trong Word.")
    if profile == "HC-ND30":
        sizes = {}
        for e in identified:
            if e.role in {"national", "motto", "date"}:
                values = {size.pt for span in e.block.runs if span.text.strip() and (size := inherited_font(span.run, "size", read.document)) is not None}
                if len(values) == 1:
                    sizes[e.role] = values.pop()
        if {"national", "motto", "date"} <= sizes.keys() and not sizes["national"]+1 == sizes["motto"] == sizes["date"]:
            issues.append(Issue(0, 0, "", "Cỡ Quốc hiệu + 1 phải bằng cỡ Tiêu ngữ và Địa danh/ngày tháng.", "ELEMENT_SIZE_CHAIN", "element", "medium", basis=p.basis+", Mục V, chú thích 1."))
    return merge_repeats(issues), identified
