import re

from .legal import BASIS_EDITORIAL, ND30, PROFILES
from .tokenizer import sentences
from .types import Issue, Suggestion, resolve_overlaps

INTERROGATIVE_FINALS = set("gì sao nào đâu không chứ à ư hả ai thế nhỉ hử hở chăng chưa".split())


def is_placeholder_gap(text, start, end):
    return 5 <= end-start <= 15 and bool(
        re.search(r"(?:ngày|tháng|năm|Số)\s*:?$", text[:start], re.I)
        or re.match(r"(?:tháng\b|năm\b|/)", text[end:], re.I))


class FormatChecker:
    def __init__(self, profile="HC-ND30"):
        self.profile = PROFILES[profile]

    def check(self, text):
        issues = []

        def add(start, end, replacement, rule, message, basis=BASIS_EDITORIAL, severity="low"):
            issues.append(Issue(start, end, text[start:end], message, rule, severity=severity,
                                suggestions=[Suggestion(replacement, message)], basis=basis))

        patterns = (
            (r" +(?=[,.;:!?])", "", "SPACE_BEFORE_PUNCT", "Bỏ dấu cách trước dấu câu."),
            (r"(?<=[(\[]) +| +(?=[)\]])", "", "SPACE_INSIDE_BRACKET", "Bỏ dấu cách sát phía trong ngoặc."),
            (r" {2,}", " ", "SPACE_MULTI", "Chỉ cần một dấu cách giữa các từ."),
            (r"[ \t]+$", "", "TRAILING_SPACE", "Bỏ khoảng trắng cuối dòng."),
            (r"^ +", "", "LEADING_SPACE", "Nên dùng thụt lề thay cho dấu cách đầu dòng."),
            (r"[\u200b\u200c\u200d\ufeff]", "", "INVISIBLE_CHARS", "Bỏ ký tự vô hình."),
            (r"(?<=\S)\t+", " ", "TAB_IN_TEXT", "Kiểm tra tab ở giữa nội dung."),
            (r"\n{3,}", "\n\n", "BLANK_LINE", "Giảm các dòng trống liên tiếp."),
        )
        for pattern, replacement, rule, message in patterns:
            for m in re.finditer(pattern, text, re.M):
                if rule == "SPACE_MULTI" and is_placeholder_gap(text, m.start(), m.end()):
                    continue
                add(m.start(), m.end(), replacement, rule, message)
        for m in re.finditer(r"([!?;,])\1+|\.{4,}", text):
            add(m.start(), m.end(), "…" if m.group().startswith(".") else m.group()[0], "PUNCT_REPEAT", "Kiểm tra dấu câu lặp lại.")
        # Punctuation inside URLs, emails, abbreviations and decimals is not spacing evidence.
        protected = [m.span() for m in re.finditer(r"https?://\S+|\S+@\S+|\b\d+[.,]\d+|\b(?:[A-Za-zĐđ]/[A-Za-z]|[A-ZĐ]{1,4}\.)", text)]
        for m in re.finditer(r"[,;:!?](?=[^\W\d_])|\.(?=[A-ZÀ-Ỹ])", text):
            if not any(a <= m.start() < b for a, b in protected):
                add(m.start(), m.end(), m.group()+" ", "MISSING_SPACE_AFTER_PUNCT", "Thêm dấu cách sau dấu câu.")
        for m in re.finditer(r"(?<=\d)(?:kg|km|cm|mm|m²|m³|ha|ml)\b", text):
            add(m.start(), m.end(), " "+m.group(), "SPACE_BEFORE_UNIT", "Thêm dấu cách trước ký hiệu đơn vị.")
        for tokens in sentences(text):
            first, last = tokens[0], tokens[-1]
            # Paragraph or true sentence start; a colon need not introduce a new sentence.
            if first.text[:1].islower():
                basis = "Nghị định 30/2020/NĐ-CP, Phụ lục II, Mục I." if self.profile.code == "HC-ND30" else BASIS_EDITORIAL
                add(first.start, first.end, first.text[:1].upper()+first.text[1:], "LOWERCASE_SENTENCE_START", "Viết hoa chữ đầu câu.", basis)
            tail = re.match(r"\s*\.", text[last.end:])
            if len(tokens) >= 2 and last.lower in INTERROGATIVE_FINALS and tail:
                pos = last.end+tail.end()-1
                add(pos, pos+1, "?", "QUESTION_MARK", "Câu kết thúc bằng từ nghi vấn; cân nhắc dùng dấu hỏi.", severity="medium")
        for m in re.finditer(r"\b(phần|chương|tiểu mục|mục|điều)(\s+[0-9IVX]+[a-z]?\b)", text):
            if self.profile.code == "HC-ND30":
                add(m.start(1), m.end(1), m.group(1).capitalize(), "CITATION_LOWERCASE", "Kiểm tra viết hoa tên phần/chương/mục/điều khi viện dẫn văn bản.", "Nghị định 30/2020/NĐ-CP, Phụ lục II, Mục V.7.")
        for m in re.finditer(r"\b(ngày|tháng) ([1-9])\b", text):
            if m.group(1) == "ngày" or int(m.group(2)) <= 2:
                basis = ND30+", Mục II.4.b." if self.profile.code == "HC-ND30" else self.profile.basis+", Phần II, I.4.2.2."
                add(m.start(2), m.end(2), "0"+m.group(2), "DATE_FORMAT", "Ngày dưới 10 và tháng 1, 2 cần thêm số 0.", basis)
        all_authorities = {x for p in PROFILES.values() for x in p.authority}
        for authority in sorted(all_authorities-set(self.profile.authority)):
            for m in re.finditer(r"(?m)^\s*("+re.escape(authority)+r")(?=\s|$)", text):
                alternatives = {"TM.": "T/M", "KT.": "K/T", "TL.": "T/L", "T/M": "TM.", "K/T": "KT.", "T/L": "TL."}
                replacement = alternatives.get(authority)
                if replacement:
                    suffix = ", Mục II.7.b." if self.profile.code == "HC-ND30" else ", Phần II, I.7.1.1."
                    add(m.start(1), m.end(1), replacement, "SIGNING_AUTHORITY", "Ký hiệu quyền hạn chưa phù hợp hồ sơ văn bản.", self.profile.basis+suffix, "medium")
                else:
                    issues.append(Issue(m.start(1), m.end(1), m.group(1), "Ký hiệu này không có trong hồ sơ quyền hạn ký; cần kiểm tra thẩm quyền, không tự đổi ký hiệu.", "SIGNING_AUTHORITY", severity="medium", basis=self.profile.basis+", Phần II, I.7.1.1."))
        if self.profile.code == "DANG-HD05":
            for m in re.finditer(r"(?m)^([ \t]*)V/v[ \t]*", text):
                start = m.start()+len(m.group(1))
                add(start, m.end(), "về việc ", "PARTY_NO_VV", "Trích yếu công văn Đảng trình bày theo mẫu “về việc…”, không viết tắt V/v.", self.profile.basis+", Phần II, I.5.2.3; Phụ lục 2, mục 5.", "medium")
            for m in re.finditer(r"(?m)^Số[ \t]*:?[ \t]*(\d+)[ \t]*-[ \t]*([A-ZĐ0-9]+/[A-ZĐ0-9/-]+)[ \t]*$", text):
                replacement = f"Số {int(m.group(1)):02d}-{m.group(2)}"
                if m.group() != replacement:
                    add(m.start(), m.end(), replacement, "PARTY_NUMBER_FORMAT", "Số và ký hiệu theo mẫu Số 05-HD/VPTW; số dưới 10 thêm 0.", self.profile.basis+", Phần II, I.3.2.2; Phụ lục 2, mục 3.", "medium")
        return resolve_overlaps(issues)

    def fix(self, text):
        for i in reversed(self.check(text)):
            text = text[:i.start] + i.suggestions[0].text + text[i.end:]
        return text
