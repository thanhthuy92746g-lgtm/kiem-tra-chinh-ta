import re

PLACE_HEAD_NOUNS = set("sông núi hồ biển cửa bến cầu vũng lạch vàm cống chợ đèo vịnh đảo suối thác bãi rừng đồi kênh mương rạch đập cảng ga phố đường thôn ấp bản làng xóm khu chùa đền đình".split())
PERSON_TITLES = ("ông", "bà", "anh", "chị", "đồng chí", "đ/c", "bác", "cụ", "giáo", "tiến sĩ", "đại tá", "thượng tá", "trung tá", "thiếu tá", "ngài", "vua", "hoàng đế", "nữ hoàng", "tổng thống", "thủ tướng")
KNOWN_PLACE_NAMES = ("Hà Nội", "Huế", "Hải Phòng", "Đà Nẵng", "Cần Thơ", "Hồ Chí Minh", "Tuyên Quang", "Cao Bằng", "Lai Châu", "Lào Cai", "Thái Nguyên", "Điện Biên", "Lạng Sơn", "Sơn La", "Phú Thọ", "Bắc Ninh", "Quảng Ninh", "Hưng Yên", "Ninh Bình", "Thanh Hóa", "Nghệ An", "Hà Tĩnh", "Quảng Trị", "Quảng Ngãi", "Gia Lai", "Khánh Hòa", "Lâm Đồng", "Đắk Lắk", "Đồng Nai", "Tây Ninh", "Đồng Tháp", "Vĩnh Long", "An Giang", "Cà Mau")
ORGANIZATION_WORDS = set("ban công sở bộ ủy uỷ hội đoàn phòng văn trường viện trung chi tổng cục đảng nhà chính quốc mặt liên học bệnh xí hợp tập ngân kho tòa toà hạt trạm đội tiểu phân".split())
STRONG_FUNCTION_WORDS = set("là thì và của có trong để với cho khi nếu mà nên nhưng hoặc".split())
LEGAL_CAPITALIZATION = "Nghị định 30/2020/NĐ-CP, Phụ lục II, Mục I và Mục III."


def is_proper_noun(tokens, index, text):
    t = tokens[index]
    if not t.text[:1].isupper():
        return False
    before = text[:t.start].rstrip().lower()
    if index and tokens[index-1].lower in PLACE_HEAD_NOUNS:
        return True
    if any(re.search(r"(?:^|\W)"+re.escape(title)+r"$", before) for title in PERSON_TITLES):
        return True
    for other in (index-1, index+1):
        if 0 <= other < len(tokens) and tokens[other].text[:1].isupper():
            a, b = sorted((index, other))
            if text[tokens[a].end:tokens[b].start].strip() in {"", "-", "–"}:
                return True
    return any(t.start >= m.start() and t.end <= m.end() for name in KNOWN_PLACE_NAMES for m in re.finditer(re.escape(name), text))


def capitalization_error(tokens, index, text, model, minimum=5000):
    t = tokens[index]
    if not t.text[:1].isupper() or t.text.isupper() or is_proper_noun(tokens, index, text):
        return False
    if t.lower in ORGANIZATION_WORDS or model.c1(t.lower) < minimum:
        return False
    if t.lower == "nhân" and index+1 < len(tokens) and tokens[index+1].lower == "dân":
        # ND30 Appendix II V.1 explicitly capitalizes Nhân dân.
        return False
    line = text[text.rfind("\n", 0, t.start)+1:text.find("\n", t.end) if "\n" in text[t.end:] else len(text)]
    if any(s in line.lower() for s in ("cộng hòa xã hội", "cộng hoà xã hội", "độc lập", "đảng cộng sản")):
        return False
    prefix = text[:t.start]
    # Newlines, sentence starts, colon/semicolon lists and bullet lists are exempt.
    if not prefix.strip() or re.search(r"[.!?…\n:;]\s*$", prefix) or re.search(r"(?:^|\n)\s*[-–+•*]\s*$", prefix):
        return False
    following = tokens[index+1].lower if index+1 < len(tokens) else ""
    return bool(re.search(r",\s*$", prefix) or following in STRONG_FUNCTION_WORDS)
