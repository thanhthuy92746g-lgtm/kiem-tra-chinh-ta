import re
from dataclasses import dataclass

from .normalize import index_map, needs_reindex, nfc

VI_LOWER = "àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ"
VI_LETTERS = "A-Za-z" + VI_LOWER + VI_LOWER.upper()
WORD = re.compile("[" + VI_LETTERS + "][" + VI_LETTERS + "0-9]*")
ABBREVIATED_TITLES = {"ts", "ths", "pgs", "gs", "tp", "tx", "tt", "nxb", "tm", "kt", "tl", "tuq"}


@dataclass(frozen=True)
class Token:
    text: str
    start: int
    end: int

    @property
    def lower(self):
        return self.text.lower()


def tokenize(text: str) -> list[Token]:
    return [Token(m.group(), m.start(), m.end()) for m in WORD.finditer(text)]


def sentences(text: str) -> list[list[Token]]:
    groups, current, last_end = [], [], 0
    for t in tokenize(text):
        gap = text[last_end:t.start]
        boundary = bool(re.search(r"[!?…\n]", gap))
        if current and not boundary:
            for match in re.finditer(r"\.", gap):
                position = last_end+match.start()
                if position and position+1 < len(text) and text[position-1].isdigit() and text[position+1].isdigit():
                    continue
                previous = current[-1]
                if position == previous.end and (previous.lower in ABBREVIATED_TITLES or len(previous.text) == 1 and previous.text.isupper()):
                    continue
                boundary = True
                break
        if current and boundary:
            groups.append(current)
            current = []
        current.append(t)
        last_end = t.end
    if current:
        groups.append(current)
    return groups
