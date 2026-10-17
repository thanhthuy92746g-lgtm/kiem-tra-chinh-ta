"""Create an explicitly labelled tiny demonstration model, not a production LM."""
import argparse
from pathlib import Path

from vietspell.training import build_model


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="data")
    p.add_argument("--force", action="store_true", help="Cho phép thay mô hình hiện có bằng mô hình mẫu.")
    a = p.parse_args()
    target = Path(a.out)
    if (target / "ngram.sqlite").exists() and not a.force:
        print("Giữ mô hình hiện có; không ghi đè.")
        return
    root = Path(__file__).resolve().parents[1]
    lines = (root / "resources/demo_corpus.txt").read_text(encoding="utf-8").splitlines()
    # Repetition only makes the demo's counts compatible with production thresholds.
    # It does not create linguistic coverage; metadata and UI disclose this.
    print(build_model((line for _ in range(1000) for line in lines), target,
                      sources=["VietSpell: câu minh hoạ tự soạn, lặp 1000 lần; không phải ngữ liệu đánh giá"],
                      quality="demo", min_unigram=1, min_bigram=1, min_trigram=1))


if __name__ == "__main__":
    main()
