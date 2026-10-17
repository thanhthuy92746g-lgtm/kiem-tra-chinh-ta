import argparse
import itertools
import json
import shutil
import sys
from pathlib import Path

from vietspell.training import build_model, corpus_lines


def main():
    p = argparse.ArgumentParser(description="Huấn luyện n-gram ngoại tuyến từ ngữ liệu đã tải.")
    p.add_argument("-i", "--input", action="append", required=True)
    p.add_argument("--out", default="data")
    p.add_argument("--max-articles", type=int, default=80000)
    p.add_argument("--prune-every", type=int, default=150000, help="Số câu mỗi lần ghi bộ đệm ra SQLite; chỉ loại n-gram hiếm lúc kết thúc.")
    for level, default in (("unigram", 4), ("bigram", 4), ("trigram", 5)):
        p.add_argument("--min-"+level, type=int, default=default)
    a = p.parse_args()
    if any(not Path(path).is_file() for path in a.input):
        p.error("Thiếu tệp ngữ liệu đầu vào.")
    target = Path(a.out)
    target.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(target).free < 6 * 1024**3:
        p.error("Cần ít nhất 6 GB dung lượng trống khi huấn luyện ngữ liệu thật.")
    lines = itertools.chain.from_iterable(corpus_lines(path, a.max_articles) for path in a.input)
    print(json.dumps(build_model(lines, target, sources=a.input, min_unigram=a.min_unigram,
                                 min_bigram=a.min_bigram, min_trigram=a.min_trigram,
                                 prune_every=a.prune_every,
                                 progress=lambda value: print(json.dumps(value), file=sys.stderr, flush=True)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
