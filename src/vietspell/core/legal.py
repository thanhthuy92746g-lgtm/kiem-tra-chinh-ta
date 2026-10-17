from dataclasses import dataclass

BASIS_EDITORIAL = "Chuẩn mực biên tập — không có quy định pháp quy trực tiếp."
ND30 = "Nghị định 30/2020/NĐ-CP, Phụ lục I"
HD05 = "Hướng dẫn số 05-HD/VPTW ngày 27/5/2026 của Văn phòng Trung ương Đảng"


@dataclass(frozen=True)
class LegalProfile:
    code: str
    title: str
    margins: tuple[tuple[float, float], ...]  # top, bottom, left, right, mm
    body_size: tuple[int, int]
    allowed_size: tuple[int, int]
    authority: tuple[str, ...]
    basis: str


PROFILES = {
    "HC-ND30": LegalProfile("HC-ND30", "Văn bản nhà nước — NĐ30", ((20, 25), (20, 25), (30, 35), (15, 20)), (13, 14), (11, 14), ("TM.", "KT.", "TL.", "TUQ.", "Q."), ND30),
    "DANG-HD05": LegalProfile("DANG-HD05", "Văn bản Đảng — HD05", ((20, 20), (20, 20), (30, 30), (15, 15)), (14, 15), (10, 16), ("T/M", "K/T", "T/L", "Q."), HD05),
}


def normalize_dashes(text):
    return text.translate(str.maketrans({c: "-" for c in "‐‑‒–—―−"}))
