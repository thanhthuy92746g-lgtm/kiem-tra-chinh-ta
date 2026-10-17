import os
import sys
from pathlib import Path


def data_dir() -> Path:
    if os.environ.get("VIETSPELL_DATA"):
        return Path(os.environ["VIETSPELL_DATA"]).resolve()
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "data"
    return Path(__file__).resolve().parents[2] / "data"
