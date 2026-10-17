"""Rule-generated syllables, intersected with observed corpus vocabulary."""
from functools import lru_cache

from .normalize import nfc

ONSETS = " b c k q ch d đ g gh gi h kh l m n ng ngh nh ph r s t th tr v x".split(" ")
NUCLEI = "a ă â e ê i y o ô ơ u ư ai ao au âu ay ây eo êu ia iê yê iu oa oă oe oi ôi ơi oo ua uă uâ ue uê ui uô uơ uy ưa ưi ưu ươ uya uyu uyê oai oao oay oeo uai uao uay uây ueo uêu uôi ươi ươu yêu iêu".split()
CODA_EXCEPTIONS = {("uy", "nh"), ("uy", "ch"), ("uy", "t"), ("oo", "ng")}
CODA_BASES = set("a ă â e ê i y o ô ơ u ư iê yê oa oă oe uâ uê uô uyê ươ".split())
TONES = ("", "\u0301", "\u0300", "\u0309", "\u0303", "\u0323")


def add_tone(onset: str, nucleus: str, coda: str, tone: str) -> str:
    if nucleus in {"oa", "oe", "uy"}:
        pos = 1
    elif any(v in nucleus for v in "êơôâă"):
        pos = max(i for i, c in enumerate(nucleus) if c in "êơôâă")
    elif nucleus.startswith("ươ"):
        pos = 1
    elif len(nucleus) == 1:
        pos = 0
    elif coda:
        pos = len(nucleus) - 1
    else:
        pos = max(0, len(nucleus) - 2)
    if onset == "q" and nucleus in {"ua", "uai", "uao", "uay", "ue", "ueo", "ui"}:
        pos = 1
    # gi + i / iê shares the letter i: gì, gìn, giếng (never giì).
    written_onset = "g" if onset == "gi" and nucleus.startswith("i") else onset
    return nfc(written_onset + nucleus[:pos+1] + tone + nucleus[pos+1:] + coda)


@lru_cache(maxsize=1)
def generate_syllables() -> frozenset[str]:
    words = set()
    for onset in ONSETS:
        for nucleus in NUCLEI:
            first = nucleus[0]
            if onset == "q" and first != "u":
                continue
            if onset == "q" and nucleus == "u":
                continue
            if nucleus in {"ue", "ueo"} and onset != "q":
                continue
            if onset == "c" and first in "eêiy" or onset == "k" and first not in "eêiy":
                continue
            if onset == "g" and first in "eêi" or onset == "gh" and first not in "eêi":
                continue
            if onset == "ng" and first in "eêi" or onset == "ngh" and first not in "eêi":
                continue
            codas = [""] + ("c ch m n ng nh p t".split() if nucleus in CODA_BASES else [])
            if onset == "q" and nucleus in {"ua", "uă", "ue"}:
                codas += "c m n ng nh p t".split()
            codas += [c for v, c in CODA_EXCEPTIONS if v == nucleus]
            for coda in codas:
                for tone in (TONES[1], TONES[5]) if coda in {"c", "ch", "p", "t"} else TONES:
                    words.add(add_tone(onset, nucleus, coda, tone))
                    # Both conventional placements occur in published Vietnamese:
                    # hòa/hoà, khỏe/khoẻ, hủy/huỷ. Do not call either an unknown word.
                    # The qu glide is different: quý is valid; qúy is not.
                    if not coda and nucleus in {"oa", "oe", "uy"} and onset != "q":
                        words.add(nfc(onset+nucleus[0]+tone+nucleus[1:]))
    return frozenset(words)
