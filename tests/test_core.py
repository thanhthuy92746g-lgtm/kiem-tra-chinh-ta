import sqlite3
import unicodedata as ud

import pytest

from vietspell.core.candidates import CandidateGenerator, damerau_levenshtein
from vietspell.core.ngram import NgramModel
from vietspell.core.normalize import fold_diacritics, get_tone, index_map, nfc, strip_tone
from vietspell.core.restore import DiacriticRestorer
from vietspell.core.syllable import generate_syllables
from vietspell.core.tokenizer import sentences, tokenize
from vietspell.training import build_model


@pytest.mark.parametrize("word,tone", [("tôi", "ngang"), ("đang", "ngang"), ("á", "sac"), ("à", "huyen"), ("ả", "hoi"), ("ã", "nga"), ("ạ", "nang"), ("ĐỘI", "nang")])
def test_unicode_tone(word, tone):
    assert get_tone(word) == tone
    assert get_tone(ud.normalize("NFD", word)) == tone
    assert nfc(ud.normalize("NFD", word)) == word


@pytest.mark.parametrize("word,fold", [("Đội", "Doi"), ("cống", "cong"), ("công", "cong"), ("TỰ", "TU"), ("Việt", "Viet"), ("gì", "gi")])
def test_fold_preserves_case(word, fold):
    assert fold_diacritics(word) == fold


def test_strip_only_tone():
    assert strip_tone("ĐỘI") == "ĐÔI"
    assert strip_tone("cống") == "công"


def test_index_mapping_combining_clusters():
    raw = "😀 " + ud.normalize("NFD", "Ông Đội")
    normalized = nfc(raw)
    mapping = index_map(raw)
    assert len(mapping) == len(normalized)
    start, end = normalized.index("Đội"), len(normalized)
    assert nfc(raw[mapping[start][0]:mapping[end-1][1]]) == "Đội"


def test_uppercase_tokenizer_and_exact_spans():
    text = "Ông ĐỘI gặp bà Ấm tại Hà Nội."
    tokens = tokenize(text)
    assert [t.text for t in tokens] == ["Ông", "ĐỘI", "gặp", "bà", "Ấm", "tại", "Hà", "Nội"]
    assert all(text[t.start:t.end] == t.text for t in tokens)


@pytest.mark.parametrize("word", ["ăn", "gì", "gìn", "giếng", "quan", "quốc", "quá", "quả", "quái", "quen", "quẻ", "quét", "quẹo", "quỉ", "huỳnh", "huỵch", "huýt", "xoong", "ngoằn", "nghiêng", "ghế", "kính", "cổng", "yên", "yết", "hòa", "hoà", "khỏe", "khoẻ", "hủy", "huỷ", "khuỷu"])
def test_attested_syllables(word):
    assert word in generate_syllables()


@pytest.mark.parametrize("word", ["ngê", "gế", "cê", "ka", "qan", "bàt", "bãc", "giì", "qúy"])
def test_disallowed_syllables(word):
    assert word not in generate_syllables()


@pytest.mark.parametrize("a,b,d", [("chào", "chào", 0), ("ban", "bna", 1), ("abc", "ac", 1), ("abc", "adc", 1), ("ab", "ba", 1), ("x", "abcd", 3), ("ca", "abc", 2), ("abc", "ca", 2)])
def test_edit_distance(a, b, d):
    assert damerau_levenshtein(a, b) == d


def test_splits_and_confusion_candidates():
    generator = CandidateGenerator({"xin", "chào", "sử", "xử", "bảo", "bão"})
    assert "xin chào" in generator.cheap("xinchào")
    assert "xử" in generator.cheap("sử")
    assert "bão" in generator.cheap("bảo")


def test_read_only_model_and_probability(model):
    assert 0 < model.p3("chưa_gặp", "cặp_lạ", "tôi") < 1
    assert model.p3("chưa_gặp", "cặp_lạ", "tôi") == model.p1("tôi")
    with pytest.raises(sqlite3.OperationalError):
        model.db.execute("DELETE FROM unigram")


def test_fixed_interpolation_unseen_trigram(tmp_path):
    # A frequent pair followed by an unseen continuation must retain 35% backoff.
    path = tmp_path / "ngram.sqlite"
    from vietspell.training import SCHEMA
    db = sqlite3.connect(path)
    db.executescript(SCHEMA)
    db.executemany("INSERT INTO unigram VALUES (?,?)", [("có", 10000), ("biết", 10000), ("sửa", 10000)])
    db.executemany("INSERT INTO bigram VALUES (?,?,?)", [("có", "biết", 9000), ("biết", "sửa", 8000)])
    db.executemany("INSERT INTO meta VALUES (?,?)", [("total_syllables", "30000"), ("lexicon_size", "3")])
    db.commit()
    db.close()
    with NgramModel(path) as m:
        assert m.p2("biết", "sửa") == pytest.approx(0.75*0.8+0.25*m.p1("sửa"))
        assert m.p3("có", "biết", "sửa") == pytest.approx(0.35*m.p2("biết", "sửa"))


def test_diacritic_frequency_and_tone_freeze(model):
    r = DiacriticRestorer(model)
    assert r.variants("bảo") == ["bảo"]
    assert "tới" not in r.variants("tôi")
    assert "ăn" in r.variants("an")
    assert len(r.variants("co")) <= 12
    assert r.restore(["tôi", "đang", "di", "chơi"], frozen={2}) == []


def test_unknown_word_uses_constant_score(model, monkeypatch):
    r = DiacriticRestorer(model)
    original = model.logprob
    def guarded(context, word):
        assert word in model.lexicon
        return original(context, word)
    monkeypatch.setattr(model, "logprob", guarded)
    assert r.score(["zz_unknown"]) == -6.0
    r.restore(["zz_unknown", "tôi"])


def test_threshold_increases_for_long_changed_runs(model, monkeypatch):
    r = DiacriticRestorer(model, min_delta=1.0)
    # A 1.5-point gain is enough for one/two edits, insufficient for three edits.
    monkeypatch.setattr(r, "score", lambda words, *args: 1.5 if "new" in words else 0)
    assert r._diff(["old", "old", "old"], ["new", "new", "new"]) == []
    assert len(r._diff(["old", "old"], ["new", "new"])) == 2


def test_batch_training_does_not_discard_global_counts(tmp_path):
    build_model(["Bạn có biết."]*5, tmp_path, sources=["test"], min_unigram=4, min_bigram=4, min_trigram=5, prune_every=1)
    with NgramModel(tmp_path / "ngram.sqlite") as m:
        assert m.c3("bạn", "có", "biết") == 5
        assert m.c1("bạn") == 5
        assert m.total == 15


@pytest.mark.parametrize("word", ["abcd", "badc", "ban", "bạn", "chào", "ab", "a", "xinchào", "aaaaaaaaaaaaaaaaaaaa"])
def test_indexed_fuzzy_search_matches_exhaustive_distance(word):
    lexicon = {"abcd", "badc", "abdc", "acbd", "ban", "bàn", "bạn", "bna", "chào", "xin", "ab", "a", "b", ""}
    generator = CandidateGenerator(lexicon)
    expected = {candidate for candidate in lexicon if candidate != word and damerau_levenshtein(word, candidate) <= 2}
    assert set(generator.fuzzy(word)) == expected


def test_sentence_boundaries_respect_decimals_and_abbreviated_titles():
    groups = sentences("TS. Nguyễn Văn An nói tỷ lệ là 25.4 phần trăm. Tôi đồng ý.")
    assert [[t.text for t in group] for group in groups] == [["TS", "Nguyễn", "Văn", "An", "nói", "tỷ", "lệ", "là", "phần", "trăm"], ["Tôi", "đồng", "ý"]]
