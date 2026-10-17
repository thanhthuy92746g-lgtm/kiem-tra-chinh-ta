"""Small, explicit press-corpus pilot. Network work never runs in the app.

RSS descriptions are discovery metadata only. Full article paragraphs are
required for training; source-use review and robots rules precede collection.
"""
import argparse
import hashlib
import json
import random
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

from lxml import html

from prepare_corpus import sentence_key, text_sentences
from vietspell.core.tokenizer import tokenize

POLICE_PLAN = json.loads((Path(__file__).resolve().parents[1] / "resources/police-pilot.json").read_text(encoding="utf-8"))
POLICE_LIMITS = {row["host"]: row["max_articles"] for row in POLICE_PLAN["sources"]}
POLICE_HOSTS = tuple(POLICE_LIMITS)
POLICE_LIMITS.update({host: POLICE_PLAN["other_provinces"]["max_articles_per_source"]
                      for host in POLICE_PLAN["other_provinces"]["hosts"]})
HOSTS = POLICE_HOSTS + ("baochinhphu.vn", "nhandan.vn", "baotintuc.vn")
HOSTS = tuple(dict.fromkeys(HOSTS + tuple(POLICE_LIMITS)))
AGENT = "VietSpellPilot/0.1"
MAX_BYTES = 2 * 1024**2


def canonical_url(url):
    p = urllib.parse.urlsplit(url)
    if p.scheme != "https" or p.hostname not in HOSTS or p.username or p.password or p.port not in (None, 443):
        raise ValueError("URL phải là HTTPS trên một miền báo đã chọn.")
    query = [(k, v) for k, v in urllib.parse.parse_qsl(p.query) if not k.lower().startswith("utm_") and k.lower() != "fbclid"]
    return urllib.parse.urlunsplit(("https", p.hostname, p.path or "/", urllib.parse.urlencode(query), ""))


class PublisherRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        canonical_url(newurl)  # Reject off-site, insecure and credentialed redirects.
        if urllib.parse.urlsplit(newurl).hostname != urllib.parse.urlsplit(req.full_url).hostname:
            raise ValueError("Chuyển sang miền khác; cần kiểm tra nguồn mới trước.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class PublisherClient:
    def __init__(self):
        self.opener = urllib.request.build_opener(PublisherRedirect())
        self.robots = {}
        self.last = {}

    def _get(self, url, delay=2):
        url = canonical_url(url)
        host = urllib.parse.urlsplit(url).hostname
        if delay > 15:
            raise ValueError("Nguồn yêu cầu crawl-delay dài; không thu thập trong lượt thử này.")
        remaining = delay-(time.monotonic()-self.last.get(host, 0))
        if remaining > 0:
            time.sleep(remaining)
        request = urllib.request.Request(url, headers={"User-Agent": AGENT, "Accept-Encoding": "identity"})
        try:
            with self.opener.open(request, timeout=20) as response:
                body = response.read(MAX_BYTES+1)
                if len(body) > MAX_BYTES:
                    raise ValueError("Tài liệu vượt giới hạn 2 MiB của pilot.")
                return body, response.headers.get_content_charset() or "utf-8"
        finally:
            self.last[host] = time.monotonic()

    def fetch(self, url):
        url = canonical_url(url)
        host = urllib.parse.urlsplit(url).hostname
        if host not in self.robots:
            parser = urllib.robotparser.RobotFileParser()
            try:
                content, encoding = self._get(f"https://{host}/robots.txt", delay=0)
                parser.parse(content.decode(encoding, errors="replace").splitlines())
            except urllib.error.HTTPError as error:
                if error.code != 404:
                    raise
                parser.parse([])  # RFC 9309: absent robots, not a connection failure.
            self.robots[host] = parser
        parser = self.robots[host]
        if not parser.can_fetch(AGENT, url):
            raise ValueError("robots.txt không cho phép đường dẫn này.")
        body, encoding = self._get(url, delay=max(2, parser.crawl_delay(AGENT) or 0))
        return body.decode(encoding, errors="replace")


def discover_feeds(page, page_url):
    tree = html.fromstring(page)
    links = tree.xpath('//link[contains(@type,"rss") or contains(@type,"atom")]/@href')
    result = []
    for link in links:
        try:
            result.append(canonical_url(urllib.parse.urljoin(page_url, link)))
        except ValueError:
            pass
    return sorted(set(result))


def parse_feed(content):
    if "<!DOCTYPE" in content.upper() or "<!ENTITY" in content.upper():
        raise ValueError("Không nhận RSS có khai báo DTD/entity.")
    root = ET.fromstring(content)
    result = []
    for entry in root.iter():
        if entry.tag.rsplit("}", 1)[-1] not in {"item", "entry"}:
            continue
        fields = {child.tag.rsplit("}", 1)[-1]: child for child in entry}
        link = fields.get("link")
        if link is None:
            continue
        url = (link.get("href") or link.text or "").strip()
        try:
            url = canonical_url(url)
        except ValueError:
            continue
        title = fields.get("title")
        result.append({"url": url, "title": "" if title is None else "".join(title.itertext()).strip()})
    return list({item["url"]: item for item in result}.values())


def extract_article(page, url):
    tree = html.fromstring(page)
    for node in tree.xpath('//script[@type="application/ld+json"]'):
        if re.search(r'"isAccessibleForFree"\s*:\s*false', node.text or "", re.I):
            raise ValueError("Không thu thập nội dung giới hạn truy cập.")
    selectors = [
        '//*[contains(concat(" ",normalize-space(@class)," ")," detail-content ")]',
        '//*[contains(concat(" ",normalize-space(@class)," ")," article-body ")]',
        '//*[contains(concat(" ",normalize-space(@class)," ")," detail__content ")]',
        '//*[contains(concat(" ",normalize-space(@class)," ")," detail-content-body ")]',
        '//article',
    ]
    bodies = next((nodes for selector in selectors if (nodes := tree.xpath(selector))), [])
    if not bodies:
        raise ValueError("Chưa nhận diện thân bài; không lấy toàn trang hoặc mô tả RSS thay thế.")
    body = bodies[0]
    for node in body.xpath('.//script|.//style|.//nav|.//aside|.//footer|.//figure|.//figcaption|.//form'):
        node.drop_tree()
    for node in list(body.xpath('.//*[@class]')):
        if re.search(r"(?:related|caption|share|breadcrumb|author|advert|box-tin)", node.get("class", ""), re.I):
            if node.getparent() is not None:
                node.drop_tree()
    paragraphs = [" ".join(p.text_content().split()) for p in body.xpath('.//p')]
    paragraphs = list(dict.fromkeys(p for p in paragraphs if len(tokenize(p)) >= 6))
    text = "\n".join(paragraphs)
    if len(tokenize(text)) < 40:
        raise ValueError("Thân bài quá ngắn hoặc chỉ là bản xem trước; bỏ khỏi tập thử.")
    title = " ".join(tree.xpath('string(//h1)').split())
    return {"url": canonical_url(url), "title": title, "text": text,
            "text_sha256": hashlib.sha256(text.encode()).hexdigest(), "review_status": "unreviewed_source"}


def collect(feeds, reviews, limit, output):
    if not 1 <= limit <= 60:
        raise ValueError("Pilot chỉ thu từ 1 đến 60 bài.")
    for feed in feeds:
        host = urllib.parse.urlsplit(canonical_url(feed)).hostname
        review = reviews.get(host, {})
        if review.get("decision") != "local_pilot_only" or not review.get("basis_url") or not review.get("notes"):
            raise ValueError("Cần ghi nhận việc đọc điều kiện sử dụng nguồn trước khi thu bài: "+host)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    client, rows, events, seen = PublisherClient(), [], [], set()
    counts = {}
    for feed in feeds:
        if len(rows) >= limit:
            break
        host = urllib.parse.urlsplit(canonical_url(feed)).hostname
        try:
            items = parse_feed(client.fetch(feed))
        except Exception as error:
            events.append({"url": feed, "error": str(error)})
            continue
        for item in items:
            if len(rows) >= limit:
                break
            if counts.get(host, 0) >= POLICE_LIMITS.get(host, limit):
                break
            if item["url"] in seen or urllib.parse.urlsplit(item["url"]).hostname != host:
                continue
            seen.add(item["url"])
            try:
                page = client.fetch(item["url"])
                row = extract_article(page, item["url"])
                row.update({"retrieved_utc": datetime.now(timezone.utc).isoformat(),
                            "html_utf8_sha256": hashlib.sha256(page.encode("utf-8")).hexdigest()})
                rows.append(row)
                counts[host] = counts.get(host, 0) + 1
            except Exception as error:
                events.append({"url": item["url"], "error": str(error)})
    (output / "articles.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False)+"\n" for row in rows), encoding="utf-8")
    report = {"articles": len(rows), "articles_by_host": counts, "police_source_caps": POLICE_LIMITS,
              "events": events, "reviews": reviews, "rss_summaries_used_as_training": False}
    (output / "collection.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def prepare(rows, output, seed=92746, holdout_hosts=()):
    if len(rows) > 100:
        raise ValueError("Tối đa 100 bài trong phép thử nhỏ.")
    holdout_hosts = set(holdout_hosts)
    # Retain the held-out source's provenance when its exact sentences reappear.
    rows = sorted(rows, key=lambda r: (urllib.parse.urlsplit(r["url"]).hostname not in holdout_hosts, r["url"]))
    present_hosts = {urllib.parse.urlsplit(canonical_url(row["url"])).hostname for row in rows}
    if holdout_hosts - present_hosts:
        raise ValueError("Miền giữ riêng phải có bài trong đầu vào.")
    groups = list(range(len(rows)))

    def root(i):
        while groups[i] != i:
            i = groups[i]
        return i

    words = [[t.lower for t in tokenize(row["text"])] for row in rows]
    shingles = [{tuple(w[i:i+5]) for i in range(max(0, len(w)-4))} for w in words]
    for i in range(len(rows)):
        for j in range(i):
            union = shingles[i] | shingles[j]
            if words[i] == words[j] or union and len(shingles[i] & shingles[j])/len(union) >= 0.8:
                groups[root(i)] = root(j)
    units = sorted({root(i) for i in range(len(rows))})
    if len(units) < 5:
        raise ValueError("Cần ít nhất 5 nhóm bài khác nhau sau loại bản sao/gần trùng.")
    random.Random(seed).shuffle(units)
    n = max(1, len(units)//5)
    mapping = {g: "test" if i < n else "dev" if i < 2*n else "train" for i, g in enumerate(units)}
    if holdout_hosts:
        # Syndicated copies of a held-out province also stay out of train/dev.
        held = {root(i) for i, row in enumerate(rows)
                if urllib.parse.urlsplit(row["url"]).hostname in holdout_hosts}
        remaining = [g for g in units if g not in held]
        if len(remaining) < 3:
            raise ValueError("Cần ít nhất ba nhóm độc lập ngoài nguồn giữ riêng cho train/dev/test.")
        dev_n = max(1, len(remaining)//5)
        mapping = {g: "test" for g in held}
        mapping.update({g: "test" if i < dev_n else "dev" if i < 2*dev_n else "train"
                        for i, g in enumerate(remaining)})
    by_split = {name: [] for name in ("train", "dev", "test")}
    article_splits = {}
    for i, row in enumerate(rows):
        split = mapping[root(i)]
        article_splits[row["url"]] = split
        for text in text_sentences(row["text"]):
            if 6 <= len(tokenize(text)) <= (100 if split == "train" else 40):
                by_split[split].append({"text": text, "source_url": row["url"], "review_status": row.get("review_status", "unreviewed_source")})
    seen = set()
    removed = {}
    # Test wins over dev; both win over training. Exact common sentences cannot leak.
    for split in ("test", "dev", "train"):
        kept = []
        removed[split] = 0
        for row in by_split[split]:
            key = sentence_key(row["text"])
            if key in seen:
                removed[split] += 1
                continue
            seen.add(key)
            kept.append(row)
        by_split[split] = kept
    if not all(by_split.values()):
        raise ValueError("Một tập bị rỗng sau lọc/trừ câu trùng; cần thêm bài độc lập.")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    for split, values in by_split.items():
        (output / f"{split}.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False)+"\n" for row in values), encoding="utf-8")
        (output / f"{split}.txt").write_text("".join(row["text"]+"\n" for row in values), encoding="utf-8")
    counts_by_host = {}
    for split, values in by_split.items():
        for row in values:
            host = urllib.parse.urlsplit(row["source_url"]).hostname
            count = counts_by_host.setdefault(host, {}).setdefault(split, {"sentences": 0, "tokens": 0})
            count["sentences"] += 1
            count["tokens"] += len(tokenize(row["text"]))
    report = {"seed": seed, "article_splits": article_splits, "distinct_article_groups": len(units),
              "holdout_hosts": sorted(holdout_hosts), "counts_by_host_and_split": counts_by_host,
              "sentence_counts": {name: len(values) for name, values in by_split.items()}, "duplicates_removed": removed,
              "reviewed_clean_sentences": sum(row["review_status"] == "reviewed_clean" for values in by_split.values() for row in values),
              "note": "Whole near-duplicate article groups kept together. Check overlap against base-model training too before reporting independent news measurements."}
    (output / "manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="action", required=True)
    probe = commands.add_parser("probe")
    probe.add_argument("--out", required=True)
    probe.add_argument("--host", action="append", choices=HOSTS, help="Mặc định kiểm tra ba nguồn Công an chính.")
    gathering = commands.add_parser("collect")
    gathering.add_argument("--feed", action="append", required=True)
    gathering.add_argument("--source-review", required=True)
    gathering.add_argument("--limit", type=int, default=30)
    gathering.add_argument("--out", required=True)
    preparation = commands.add_parser("prepare")
    preparation.add_argument("--articles", required=True)
    preparation.add_argument("--out", required=True)
    preparation.add_argument("--holdout-host", action="append", default=[], choices=HOSTS,
                             help="Giữ mọi bài và bản đăng lại của miền này chỉ trong test.")
    args = parser.parse_args()
    if args.action == "probe":
        client, result = PublisherClient(), []
        for host in dict.fromkeys(args.host or POLICE_HOSTS):
            try:
                url = f"https://{host}/"
                result.append({"host": host, "feeds": discover_feeds(client.fetch(url), url)})
            except Exception as error:
                result.append({"host": host, "error": str(error)})
        with Path(args.out).open("x", encoding="utf-8") as file:
            json.dump(result, file, ensure_ascii=False, indent=2)
    elif args.action == "collect":
        result = collect(args.feed, json.loads(Path(args.source_review).read_text(encoding="utf-8")), args.limit, args.out)
    else:
        rows = [json.loads(line) for line in Path(args.articles).read_text(encoding="utf-8").splitlines() if line.strip()]
        result = prepare(rows, args.out, holdout_hosts=args.holdout_host)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
