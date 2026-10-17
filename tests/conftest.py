import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/vietspell-cache" if os.name != "nt" else str(Path(__file__).resolve().parents[1] / "_scratch/cache"))

import pytest

from vietspell.core.detector import Checker
from vietspell.core.ngram import NgramModel
from vietspell.training import build_model


@pytest.fixture(scope="session")
def model_dir(tmp_path_factory):
    path = tmp_path_factory.mktemp("demo-model")
    lines = (Path(__file__).resolve().parents[1] / "resources/demo_corpus.txt").read_text(encoding="utf-8").splitlines()
    build_model((line for _ in range(1000) for line in lines), path, sources=["test synthetic fixture"], quality="demo", min_unigram=1, min_bigram=1, min_trigram=1)
    return path


@pytest.fixture
def model(model_dir):
    with NgramModel(model_dir / "ngram.sqlite") as m:
        yield m


@pytest.fixture
def checker(model):
    return Checker(model)


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtWidgets import QApplication
    from vietspell.gui.theme import apply_theme
    app = QApplication.instance() or QApplication([])
    apply_theme(app)
    yield app
