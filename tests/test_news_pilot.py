"""Synthetic fixtures here test tooling only; never used for actual training."""
import importlib
from pathlib import Path

import pytest

from vietspell.core.tokenizer import tokenize
from vietspell.core.types import CheckResult, Issue


@pytest.fixture
def news(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]/"tools"))
    return importlib.import_module("news_pilot")


def test_rss_description_is_metadata_not_training_body(news):
    feed = '<rss><channel><item><title>Tin mới</title><link>https://nhandan.vn/bai.html?utm_source=rss</link><description>Đoạn tóm tắt không phải toàn văn.</description></item></channel></rss>'
    assert news.parse_feed(feed) == [{"url": "https://nhandan.vn/bai.html", "title": "Tin mới"}]


def test_atom_and_duplicate_links(news):
    entry = '<entry><title>Tin</title><link href="https://baochinhphu.vn/tin.htm"/></entry>'
    assert len(news.parse_feed('<feed xmlns="http://www.w3.org/2005/Atom">'+entry*2+'</feed>')) == 1


@pytest.mark.parametrize("url", ["http://nhandan.vn/a", "https://nhandan.vn.evil.example/a", "https://127.0.0.1/a", "https://user:password@nhandan.vn/a", "https://nhandan.vn:8443/a"])
def test_offsite_insecure_and_credentialed_urls_rejected(news, url):
    with pytest.raises(ValueError):
        news.canonical_url(url)


def test_entity_feed_and_offsite_redirect_rejected(news):
    with pytest.raises(ValueError):
        news.parse_feed('<!DOCTYPE rss [<!ENTITY x "test">]><rss/>')
    from urllib.request import Request
    with pytest.raises(ValueError):
        news.PublisherRedirect().redirect_request(Request('https://nhandan.vn/a'), None, 302, '', {}, 'https://example.org/a')


BODY = "Các đơn vị triển khai nhiệm vụ theo kế hoạch đã được thông qua. Người dân được hướng dẫn thực hiện thủ tục tại cơ quan có thẩm quyền. Chính quyền địa phương tổ chức hội nghị và trao đổi các giải pháp nâng cao chất lượng phục vụ."


def test_article_extraction_excludes_navigation_captions_and_related(news):
    page = f'<html><nav>NAV_LEAK</nav><article><h1>Tên bài</h1><p>{BODY}</p><figure><p>CAPTION_LEAK</p></figure><div class="related"><p>RELATED_LEAK</p></div><aside>ASIDE_LEAK</aside></article></html>'
    article = news.extract_article(page, 'https://nhandan.vn/a')
    assert article['text'] == BODY
    assert article['title'] == 'Tên bài'
    assert article['review_status'] == 'unreviewed_source'


@pytest.mark.parametrize("page", ['<html><p>'+BODY+'</p></html>', '<article><p>Đây chỉ là bản xem trước của bài.</p></article>', '<script type="application/ld+json">{"isAccessibleForFree":false}</script><article><p>'+BODY+'</p></article>'])
def test_no_fullpage_fallback_or_paywall_preview(news, page):
    with pytest.raises(ValueError):
        news.extract_article(page, 'https://baochinhphu.vn/a')


def test_collect_requires_source_review_before_creating_output(news, tmp_path):
    target = tmp_path/'collection'
    with pytest.raises(ValueError):
        news.collect(['https://nhandan.vn/home.rss'], {}, 2, target)
    assert not target.exists()


def test_police_collection_caps_each_source_across_feeds_and_keeps_reserve(news, monkeypatch, tmp_path):
    import json
    class FakeClient:
        def fetch(self, url):
            host = news.urllib.parse.urlsplit(url).hostname
            if url.endswith('.rss'):
                # Enough unique URLs to monopolize the entire budget without caps.
                return '<rss><channel>'+''.join(f'<item><link>https://{host}/bai-{i}</link></item>' for i in range(60))+'</channel></rss>'
            return '<article><p>'+BODY+'</p></article>'
    monkeypatch.setattr(news, 'PublisherClient', FakeClient)
    hosts = news.POLICE_HOSTS
    feeds = [f'https://{host}/tin.rss' for host in hosts]
    feeds.insert(1, f'https://{hosts[0]}/khac.rss')
    reviews = {host: {'decision':'local_pilot_only', 'basis_url':f'https://{host}/dieu-kien', 'notes':'Fixture, không phải nguồn thật.'} for host in hosts}
    result = news.collect(feeds, reviews, 60, tmp_path/'collection')
    assert result['articles_by_host'] == {hosts[0]:18, hosts[1]:18, hosts[2]:15}
    assert result['articles'] == 51  # Nine provincial articles stay reserved, not backfilled.
    rows = [json.loads(line) for line in (tmp_path/'collection/articles.jsonl').read_text().splitlines()]
    assert len(rows) == len({row['url'] for row in rows}) == 51


def test_whole_source_holdout_also_removes_cross_source_copies(news, tmp_path):
    rows = [
        {'url':'https://congan.ninhbinh.gov.vn/a', 'text':BODY},
        {'url':'https://cand.com.vn/copy', 'text':BODY+' Nhé.'},
        {'url':'https://bocongan.gov.vn/a', 'text':'Nhà khoa học nghiên cứu phương pháp bảo vệ nguồn nước và tài nguyên rừng.'},
        {'url':'https://bocongan.gov.vn/b', 'text':'Doanh nghiệp mở rộng nhà máy sản xuất linh kiện điện tử tại khu công nghiệp.'},
        {'url':'https://cand.com.vn/a', 'text':'Du khách đến tham quan di tích lịch sử và tìm hiểu đời sống cộng đồng.'},
        {'url':'https://cand.com.vn/b', 'text':'Những người nông dân thu hoạch lúa trên cánh đồng trong buổi sáng mùa hè.'},
    ]
    result = news.prepare(rows, tmp_path/'split', holdout_hosts=['congan.ninhbinh.gov.vn'])
    assert result['article_splits'][rows[0]['url']] == 'test'
    assert result['article_splits'][rows[1]['url']] == 'test'
    assert {result['article_splits'][row['url']] for row in rows[2:]} == {'train', 'dev', 'test'}
    counts = result['counts_by_host_and_split']['congan.ninhbinh.gov.vn']
    assert set(counts) == {'test'} and counts['test']['tokens'] > 0
    with pytest.raises(ValueError, match='Miền giữ riêng'):
        news.prepare(rows, tmp_path/'missing', holdout_hosts=['baotintuc.vn'])
    assert not (tmp_path/'missing').exists()


def test_article_groups_and_common_sentences_do_not_leak(news, tmp_path):
    paragraphs = [
        'Học sinh tham gia hoạt động thể thao tại trường sau những giờ học căng thẳng.',
        'Những người nông dân thu hoạch lúa trên cánh đồng trong buổi sáng mùa hè.',
        'Đoàn nghệ thuật biểu diễn chương trình âm nhạc truyền thống phục vụ khán giả.',
        'Các bác sĩ sử dụng thiết bị hiện đại để khám bệnh và chăm sóc sức khỏe.',
        'Tuyến đường sắt kết nối nhiều thành phố giúp vận chuyển hàng hóa thuận tiện.',
        'Nhà khoa học nghiên cứu phương pháp bảo vệ nguồn nước và tài nguyên rừng.',
        'Doanh nghiệp mở rộng nhà máy sản xuất linh kiện điện tử tại khu công nghiệp.',
        'Du khách đến tham quan di tích lịch sử và tìm hiểu đời sống cộng đồng.',
    ]
    common = 'Các đơn vị thực hiện nhiệm vụ theo quy định.'
    rows = [{'url':f'https://nhandan.vn/bai-{i}', 'text':p+'\n'+common} for i,p in enumerate(paragraphs)]
    rows.append({**rows[0], 'url':'https://baochinhphu.vn/ban-dang-lai'})
    rows.append({**rows[0], 'url':'https://baotintuc.vn/ban-gan-trung', 'text':rows[0]['text']+' Nhé.'})
    report = news.prepare(rows, tmp_path/'split')
    assert report['article_splits'][rows[0]['url']] == report['article_splits'][rows[-1]['url']]
    assert report['article_splits'][rows[0]['url']] == report['article_splits'][rows[-2]['url']]
    keys = {}
    for name in ('train','dev','test'):
        keys[name] = {news.sentence_key(line) for line in (tmp_path/'split'/f'{name}.txt').read_text().splitlines()}
    assert all(keys.values())
    assert not (keys['train'] & keys['test'] or keys['train'] & keys['dev'] or keys['dev'] & keys['test'])
    assert report['reviewed_clean_sentences'] == 0


def test_model_comparison_uses_fixed_cases_and_does_not_call_unreviewed_findings_false_positive(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]/'tools'))
    comparison = importlib.import_module('compare_models')
    text = 'Tôi đang đi học ở trường.'
    frozen = comparison.freeze_cases([{'text':text,'review_status':'unreviewed_source'}],{t.lower for t in tokenize(text)})

    class Recorder:
        def __init__(self, unknown): self.seen=[]; self.unknown=unknown
        def check(self, text):
            self.seen.append(text)
            findings=[Issue(0,len(text),text,'Unknown source','UNKNOWN','unknown')] if self.unknown else []
            return CheckResult(text,findings)

    first, second = Recorder(False), Recorder(True)
    a, b = comparison.measure(first,frozen), comparison.measure(second,frozen)
    assert first.seen == second.seen
    assert a['source_sentences_with_findings'] == 0 and b['source_sentences_with_findings'] == 1
    assert b['reviewed_false_positive_sentence_rate'] is None
    assert all(a['synthetic_corruptions'][k]['cases']==b['synthetic_corruptions'][k]['cases'] for k in a['synthetic_corruptions'])
