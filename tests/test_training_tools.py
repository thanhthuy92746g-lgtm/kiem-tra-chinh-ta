import bz2
import gzip
import importlib.util
import importlib
import shutil
from pathlib import Path


def preparation_module():
    path = Path(__file__).resolve().parents[1] / "tools/prepare_corpus.py"
    spec = importlib.util.spec_from_file_location("prepare_corpus_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_wiki_cleanup_keeps_prose_and_names():
    module = preparation_module()
    raw = "{{Mẫu|a={{Mẫu con|x}}}} '''Hà Nội''' là [[Thủ đô|thủ đô]] Việt Nam.<ref>Thông tin nguồn.</ref>\n== Tham khảo ==\nNguồn không phải nội dung."
    cleaned = module.clean_wiki(raw)
    assert "Hà Nội là thủ đô Việt Nam." in cleaned
    assert not any(s in cleaned for s in ("Mẫu", "nguồn", "[[", "{{", "Tham khảo"))


def test_heldout_is_removed_across_training_sources(tmp_path):
    module = preparation_module()
    first = ["Hôm nay bạn ăn cơm cùng gia đình.", "Tôi đang đi học ở trường cùng bạn.", "Bạn có biết cách sửa văn bản này không?"]
    other = "Chính quyền địa phương thực hiện công tác bảo vệ an ninh và trật tự xã hội."
    pages = []
    for i, text in enumerate((" ".join(first), other*3, other*3)):
        pages.append(f"<page><title>Bài {i}</title><ns>0</ns><revision><text>{text}</text></revision></page>")
    wiki = tmp_path / "wiki.xml.bz2"
    wiki.write_bytes(bz2.compress(("<mediawiki xmlns='urn:test'>"+"".join(pages)+"</mediawiki>").encode()))
    opus = tmp_path / "opus.txt.gz"
    dialogue = ["Tôi rất vui khi được gặp bạn hôm nay.", "Chúng ta sẽ cùng nhau hoàn thành công việc.", "Bạn hãy đến đây để cùng trao đổi nhé."]
    with gzip.open(opus, "wt", encoding="utf-8") as file:
        file.write("\n".join(dialogue+first+[other]))
    target = tmp_path / "prepared"
    report = module.prepare(wiki, opus, target, max_articles=2, heldout_count=3)
    assert report["heldout_counts"] == {"wiki": 3, "opus": 3}
    assert report["training"]["wiki_articles"] == 2
    heldout_keys = {module.sentence_key(s) for kind in ("wiki", "opus") for s in (target/f"{kind}-heldout.txt").read_text(encoding="utf-8").splitlines()}
    training = [s for kind in ("wiki", "opus") for s in (target/f"{kind}-train.txt").read_text(encoding="utf-8").splitlines()]
    assert training
    assert all(module.sentence_key(s) not in heldout_keys for s in training)
    assert report["training"]["excluded_duplicates"] == 3


def test_prepared_sentences_preserve_decimal_and_closing_parenthesis():
    module = preparation_module()
    result = list(module.text_sentences("Tỷ lệ đạt 25.4 phần trăm (theo báo cáo). Tôi đồng ý."))
    assert result == ["Tỷ lệ đạt 25.4 phần trăm (theo báo cáo).", "Tôi đồng ý."]


def test_model_promotion_preserves_whitelist_and_backups(tmp_path, model_dir, monkeypatch):
    tools = Path(__file__).resolve().parents[1] / "tools"
    monkeypatch.syspath_prepend(str(tools))
    promote = importlib.import_module("promote_model").promote
    target = tmp_path / "installed"
    target.mkdir()
    original = b"previous model preserved byte for byte"
    (target / "ngram.sqlite").write_bytes(original)
    (target / "whitelist.txt").write_text("TừRiêng\n", encoding="utf-8")
    result = promote(model_dir, target)
    assert (Path(result["backup"]) / "ngram.sqlite").read_bytes() == original
    assert (target / "whitelist.txt").read_text(encoding="utf-8") == "TừRiêng\n"
    assert (target / "ngram.sqlite").read_bytes() == (model_dir / "ngram.sqlite").read_bytes()


def test_mismatched_vocabulary_cannot_replace_current_model(tmp_path, model_dir, monkeypatch):
    import pytest
    tools = Path(__file__).resolve().parents[1] / "tools"
    monkeypatch.syspath_prepend(str(tools))
    promote = importlib.import_module("promote_model").promote
    candidate = tmp_path / "candidate"
    shutil.copytree(model_dir, candidate)
    (candidate / "syllables.txt").write_text("wrong-vocabulary\n", encoding="utf-8")
    target = tmp_path / "installed"
    target.mkdir()
    (target / "ngram.sqlite").write_bytes(b"current")
    with pytest.raises(ValueError, match="không khớp"):
        promote(candidate, target)
    assert (target / "ngram.sqlite").read_bytes() == b"current"
