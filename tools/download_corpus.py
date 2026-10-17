"""Explicit network utility. The application itself never downloads data."""
import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

SOURCES = {
    "viwiki": ("https://dumps.wikimedia.org/viwiki/latest/viwiki-latest-pages-articles.xml.bz2", "viwiki-pages-articles.xml.bz2"),
    "opensubtitles": ("https://object.pouta.csc.fi/OPUS-OpenSubtitles/v2018/mono/vi.txt.gz", "opus-opensubtitles-vi.txt.gz"),
    "ccaligned": ("https://object.pouta.csc.fi/OPUS-CCAligned/v1/mono/vi.txt.gz", "opus-ccaligned-vi.txt.gz"),
}
USER_AGENT = "VietSpell/0.1 corpus preparation (offline Vietnamese document checker)"


def open_source(url):
    # Wikimedia rejects anonymous Python-urllib requests; identify the actual tool.
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": USER_AGENT}), timeout=60)


def wikipedia_source():
    checksums_url = "https://dumps.wikimedia.org/viwiki/latest/viwiki-latest-md5sums.txt"
    with open_source(checksums_url) as response:
        lines = response.read().decode("utf-8").splitlines()
    entries = [line.split() for line in lines if line.endswith("-pages-articles.xml.bz2")]
    if len(entries) != 1:
        raise ValueError("Không xác định được checksum bản dump Wikipedia; không bỏ qua xác minh.")
    expected, filename = entries[0]
    version = filename.split("-")[1]
    return f"https://dumps.wikimedia.org/viwiki/{version}/{filename}", expected, checksums_url


def main():
    p = argparse.ArgumentParser(description="Tải ngữ liệu có chủ đích, chỉ dùng lúc phát triển.")
    p.add_argument("sources", nargs="+", choices=SOURCES)
    p.add_argument("--out", default="data/raw")
    a = p.parse_args()
    root = Path(a.out)
    root.mkdir(parents=True, exist_ok=True)
    for name in a.sources:
        url, filename = SOURCES[name]
        expected_md5, checksum_url = None, None
        if name == "viwiki":
            url, expected_md5, checksum_url = wikipedia_source()
        dest = root / filename
        if dest.exists():
            raise FileExistsError(f"Đã có {dest}; không ghi đè ngữ liệu cũ.")
        temp = dest.with_suffix(dest.suffix+".part")
        digest = hashlib.sha256()
        md5 = hashlib.md5(usedforsecurity=False)
        received, reported = 0, 0
        try:
            with open_source(url) as response, temp.open("wb") as output:
                while block := response.read(1024*1024):
                    digest.update(block)
                    md5.update(block)
                    output.write(block)
                    received += len(block)
                    if received-reported >= 64*1024**2:
                        print(f"{name}: {received/1024**2:.0f} MiB", file=sys.stderr, flush=True)
                        reported = received
            if expected_md5 is not None and md5.hexdigest() != expected_md5:
                raise ValueError("Checksum Wikipedia không khớp; không sử dụng bản tải này.")
            temp.replace(dest)
        except BaseException:
            temp.unlink(missing_ok=True)
            raise
        # Digest records the transfer, it is not an independently trusted publisher checksum.
        dest.with_suffix(dest.suffix+".source.json").write_text(json.dumps({"url": url, "sha256": digest.hexdigest(),
            "publisher_md5": expected_md5, "checksum_source": checksum_url,
            "publisher_checksum_verified": expected_md5 is not None}, indent=2), encoding="utf-8")
        print(f"Đã tải {dest}")


if __name__ == "__main__":
    main()
