import unicodedata as ud

TONE_MARKS = {"\u0301": "sac", "\u0300": "huyen", "\u0309": "hoi",
              "\u0303": "nga", "\u0323": "nang"}


def nfc(text: str) -> str:
    return ud.normalize("NFC", text)


def strip_tone(word: str) -> str:
    return nfc("".join(c for c in ud.normalize("NFD", word) if c not in TONE_MARKS))


def get_tone(word: str) -> str:
    return next((TONE_MARKS[c] for c in ud.normalize("NFD", word) if c in TONE_MARKS), "ngang")


def fold_diacritics(word: str) -> str:
    return "".join(c for c in ud.normalize("NFD", word) if not ud.combining(c)).replace("đ", "d").replace("Đ", "D")


def index_map(text: str) -> list[tuple[int, int]]:
    """Map each NFC character back to its original combining-character cluster."""
    result = []
    start = 0
    while start < len(text):
        end = start + 1
        while end < len(text) and ud.combining(text[end]):
            end += 1
        result.extend([(start, end)] * len(nfc(text[start:end])))
        start = end
    return result


def needs_reindex(text: str) -> bool:
    return text != nfc(text)


def match_case(original: str, replacement: str) -> str:
    if original.isupper():
        return replacement.upper()
    if original[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement
