import socket
import unicodedata as ud

import pytest

from vietspell.core.detector import Checker
from vietspell.core.restore import DiacriticRestorer


def suggestions(checker, text):
    return [(i.text, i.suggestions[0].text) for i in checker.check(text).issues if i.editable]


def test_decisive_three_errors(checker):
    assert suggestions(checker, "Hôm nay bạn an gì. Tôi đang di chơi.") == [("an", "ăn"), (".", "?"), ("di", "đi")]


def test_no_common_word_rewriting(checker):
    assert suggestions(checker, "Tôi đang di chơi.") == [("di", "đi")]


def test_multiword_restore_and_co(checker):
    result = suggestions(checker, "Co biết sửa cai nay ko?")
    assert ("Co", "Có") in result
    assert ("cai", "cái") in result
    assert ("nay", "này") in result
    assert ("ko", "không") in result


def test_whole_unaccented_sentence(model):
    r = DiacriticRestorer(model)
    words = "toi di hoc o truong".split()
    for i, value, delta in r.restore(words):
        words[i] = value
    assert words == "tôi đi học ở trường".split()


def test_cai_nay_restoration(model):
    r = DiacriticRestorer(model)
    changes = r.restore(["cai", "nay"])
    assert [(i, word) for i, word, _ in changes] == [(0, "cái"), (1, "này")]


@pytest.mark.parametrize("text", ["Công trình cống Đôi đã hoàn thành.", "Công trình cầu Đôi đã hoàn thành.", "Ban chỉ đạo", "Công an tỉnh", "Độc lập – Tự do – Hạnh phúc", "- Như trên;", "Đại tá Lê Văn Tuấn", "Ông Nguyễn Văn Nam", "Sở Nông nghiệp", "Hà Nội", "UBND CAT-ANKT Đ/c V/v", "VietSpell iPhone macOS", "Tôi không biết gì cả."])
def test_false_positive_regressions(checker, text):
    assert not [i for i in checker.check(text).issues if i.kind in {"capitalization", "diacritic"}]


def test_doi_entire_sentence_clean(checker):
    assert checker.check("Công trình cống Đôi đã hoàn thành.").issues == []


def test_nhat_is_not_a_place_name(checker):
    result = checker.check("Trong công tác, Nhất là công tác giải phóng mặt bằng.")
    errors = [i for i in result.issues if i.rule_id == "CAPITALIZATION"]
    assert [(i.text, i.suggestions[0].text) for i in errors] == [("Nhất", "nhất")]


def test_all_caps_administrative_abbreviations(checker):
    assert not [i for i in checker.check("UBND TW CAT ANKT").issues if i.kind in {"abbrev", "unknown", "diacritic"}]


def test_whitelist_precedes_abbreviation_and_restore(model):
    c = Checker(model, whitelist={"ko", "di"})
    assert not [i for i in c.check("Tôi đang di chơi ko?").issues if i.text in {"ko", "di"}]


def test_nfd_input_normalized_without_span_drift(checker):
    result = checker.check(ud.normalize("NFD", "Hôm nay bạn an gì. Tôi đang di chơi."))
    assert result.text == "Hôm nay bạn an gì. Tôi đang di chơi."
    assert all(result.text[i.start:i.end] == i.text for i in result.issues)


def test_checking_never_uses_network(checker, monkeypatch):
    def forbidden(*a, **k):
        raise AssertionError("Runtime attempted network access")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    assert len(checker.check("Hôm nay bạn an gì. Tôi đang di chơi.").issues) == 3


def test_context_and_confusion_are_distinct(checker):
    results = checker.check("An ninh minh tế. Tôi sẽ sử lý hồ sơ.").issues
    assert any(i.rule_id == "CONTEXT" and i.text == "minh" and i.suggestions[0].text == "kinh" for i in results)
    assert any(i.rule_id == "CONFUSION" and i.text == "sử" and i.suggestions[0].text == "xử" for i in results)


def test_nhan_dan_legal_exception(checker):
    assert not any(i.rule_id == "CAPITALIZATION" and i.text == "Nhân" for i in checker.check("Các cơ quan, Nhân dân và Nhà nước cùng thực hiện.").issues)


@pytest.mark.parametrize("text,protected", [
    ("Tôi gặp Margaret và Anderson.", {"Margaret", "Anderson"}),
    ("Khoảng cách là 120 km và 20 mm.", {"km", "mm"}),
    ("Trong bảng chữ cái, j và z là ký tự.", {"j", "z"}),
    ("Ký hiệu /o/ là âm được nhắc tới.", {"o"}),
    ("Một tên gọi là al-Salvador.", {"al", "Salvador"}),
    ("Tôi đang ở Hán-Nhật-Hàn-Việt.", {"Hán", "Nhật", "Hàn", "Việt"}),
])
def test_foreign_names_symbols_units_are_not_rewritten(checker, text, protected):
    assert not any(i.text in protected and i.kind in {"abbrev", "diacritic", "unknown", "context", "confusion", "fuzzy"} for i in checker.check(text).issues)


def test_vietnamese_accented_typo_still_checked(checker):
    assert any(i.text == "Hômm" and i.suggestions and i.suggestions[0].text == "Hôm" for i in checker.check("Hômm nay bạn ăn gì?").issues)
