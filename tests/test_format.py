import pytest

from vietspell.core.format_rules import FormatChecker, is_placeholder_gap
from vietspell.core.legal import BASIS_EDITORIAL


def test_overlapping_spaces_do_not_delete_final_period():
    assert FormatChecker().fix("Xin  chào các bạn   .") == "Xin chào các bạn."


@pytest.mark.parametrize("source,expected", [("Xin chào , các bạn.", "Xin chào, các bạn."), ("Xin chào!Bạn.", "Xin chào! Bạn."), ("Xin chào ( bạn ).", "Xin chào (bạn)."), ("Xin chào!!", "Xin chào!"), ("Xin chào.  ", "Xin chào."), ("Xin\u200b chào.", "Xin chào."), ("Nặng 20kg.", "Nặng 20 kg."), ("ngày 2 tháng 1 năm 2026", "Ngày 02 tháng 01 năm 2026")])
def test_format_corrections(source, expected):
    assert FormatChecker().fix(source) == expected


@pytest.mark.parametrize("count", [5, 9, 15])
def test_signature_placeholders_exempt(count):
    for text in ("Số:"+" "*count+"/CAT-ANKT", "Ninh Bình, ngày"+" "*count+"tháng 10 năm 2026"):
        assert not [i for i in FormatChecker().check(text) if i.rule_id == "SPACE_MULTI"]


@pytest.mark.parametrize("count", [2, 4, 16])
def test_arbitrary_gaps_still_reported(count):
    text = "Xin"+" "*count+"chào."
    assert any(i.rule_id == "SPACE_MULTI" for i in FormatChecker().check(text))


def test_question_mark_only_sentence_final():
    assert not [i for i in FormatChecker().check("Tôi không biết gì cả.") if i.rule_id == "QUESTION_MARK"]
    result = [i for i in FormatChecker().check("Bạn ăn gì.") if i.rule_id == "QUESTION_MARK"]
    assert len(result) == 1 and result[0].suggestions[0].text == "?"
    assert "không có quy định pháp quy trực tiếp" in result[0].basis


def test_editorial_rules_do_not_claim_legal_authority():
    result = FormatChecker().check("Xin  chào , bạn!Tôi đây.")
    assert result
    assert all(i.basis == BASIS_EDITORIAL for i in result)


def test_signing_authority_profiles():
    assert any(i.rule_id == "SIGNING_AUTHORITY" for i in FormatChecker().check("T/M GIÁM ĐỐC"))
    assert not any(i.rule_id == "SIGNING_AUTHORITY" for i in FormatChecker().check("TM. GIÁM ĐỐC"))
    assert any(i.rule_id == "PARTY_NO_VV" for i in FormatChecker("DANG-HD05").check("V/v thực hiện kế hoạch"))


def test_urls_decimals_and_acronyms_not_spacing_errors():
    result = FormatChecker().check("Xem https://example.org/a:b và số 1,5 tại P.1.")
    assert not any(i.rule_id == "MISSING_SPACE_AFTER_PUNCT" for i in result)


def test_citations_do_not_force_khoan_diem_uppercase():
    result = FormatChecker().check("Căn cứ điều 5, khoản 2 và điểm a.")
    assert [(i.text, i.suggestions[0].text) for i in result if i.rule_id == "CITATION_LOWERCASE"] == [("điều", "Điều")]
