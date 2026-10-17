import re
from dataclasses import dataclass

from .abbrev import ABBREVIATIONS
from .candidates import CandidateGenerator, damerau_levenshtein
from .format_rules import FormatChecker
from .normalize import fold_diacritics, get_tone, match_case, nfc, strip_tone
from .proper_nouns import LEGAL_CAPITALIZATION, capitalization_error, is_proper_noun
from .restore import DiacriticRestorer
from .syllable import generate_syllables
from .tokenizer import sentences
from .types import CheckResult, Issue, Suggestion, resolve_overlaps

SENSITIVITY_PRESETS = {"Chặt — ít báo nhầm": (6.0, 9.0, 2.5), "Cân bằng — khuyên dùng": (2.5, 4.0, 1.0), "Nhạy — bắt nhiều lỗi": (2.0, 3.5, 0.8)}
UNITS = set("km mm cm dm m kg g mg ha ml l s ms hz khz mhz ghz kb mb gb tb bit byte".split())
SECOND_EDIT_PENALTY = 2.0  # 100x lower prior for a second arbitrary character edit.


@dataclass
class CheckerConfig:
    context_threshold: float = -3.0
    min_delta_confusion: float = 2.5
    min_delta_fuzzy: float = 4.0
    min_delta_diacritic: float = 1.0
    min_delta_diacritic_run: float = 1.0
    capitalization_min_count: int = 5000
    diacritic_beam: int = 8


class Checker:
    def __init__(self, model, config=None, whitelist=(), profile="HC-ND30"):
        self.model = model
        self.config = config or CheckerConfig()
        self.whitelist = {nfc(w).lower() for w in whitelist}
        self.generator = CandidateGenerator(model.lexicon)
        self.restorer = DiacriticRestorer(model, self.config.diacritic_beam, self.config.min_delta_diacritic, self.config.min_delta_diacritic_run)
        self.formats = FormatChecker(profile)

    def _skip(self, tokens, i, text):
        t = tokens[i]
        word = t.text
        if t.lower in self.whitelist:
            return True
        if re.search("[fjwz]", word, re.I):
            return True
        if word.isupper() and (t.lower not in self.model.lexicon or len(word) == 1):
            return True
        if any(c.isupper() for c in word[1:]) and not word.isupper():
            return True
        adjacent = text[max(0, t.start-1):t.start]+text[t.end:t.end+1]
        if "/" in adjacent and len(word) <= 2 or word.isupper() and any(c in adjacent for c in "/-"):
            return True
        if any(a <= t.start < b for a, b in (m.span() for m in re.finditer(r"https?://\S+|\S+@\S+", text))):
            return True
        return is_proper_noun(tokens, i, text)

    def _delta(self, words, index, replacement):
        proposed = words[:index] + replacement.split() + words[index+1:]
        return self.restorer.score(proposed, index, index+len(replacement.split())+2) - self.restorer.score(words, index, index+3)

    def _literal_spans(self, text):
        technical = bool(re.search(r"\b(?:chữ|âm|ký tự|bảng mã|ASCII|IPA)\b", text, re.I))
        spans = []
        if technical:
            spans.extend(m.span() for m in re.finditer(r'"[^"\n]+"|“[^”\n]+”|/[^/\s]+/', text))
        for m in re.finditer(r"[^\W\d_]+(?:[-'’][^\W\d_]+)+", text):
            parts = re.split(r"[-'’]", m.group())
            foreign_name = any(p[:1].isupper() and p.lower() not in self.model.lexicon and p.lower() not in generate_syllables() and not self.restorer.groups.get(fold_diacritics(p.lower())) for p in parts)
            if technical or foreign_name:
                spans.append(m.span())
        return technical, spans

    def _literal_exempt(self, token, text, technical, spans):
        word = token.text
        if any(a <= token.start and token.end <= b for a, b in spans):
            return True
        if word.isupper() and word.isascii() and len(word) <= 4:
            return True
        if token.lower in UNITS and re.search(r"\d[\d.,]*\s*$", text[:token.start]):
            return True
        if technical and len(word) == 1:
            return True
        if token.lower == "s" and text[max(0, token.start-1):token.start] in {"'", "’"}:
            return True
        if (word[:1].isupper() or technical) and word.isascii() and token.lower not in self.model.lexicon and token.lower not in generate_syllables():
            # Foreign proper names / technical words are not malformed Vietnamese
            # syllables. Keep a path for unaccented Vietnamese such as Truong.
            return not self.restorer.groups.get(fold_diacritics(token.lower))
        return False

    def check(self, text):
        text = nfc(text)
        issues = self.formats.check(text)
        technical, literal_spans = self._literal_spans(text)
        for tokens in sentences(text):
            words = [t.lower for t in tokens]
            frozen = set()
            handled = set()
            for i, t in enumerate(tokens):
                if self._literal_exempt(t, text, technical, literal_spans):
                    frozen.add(i)
                # Abbreviations have priority over the general foreign-letter rule.
                elif t.lower in ABBREVIATIONS and not t.text.isupper() and t.lower not in self.whitelist:
                    replacement = match_case(t.text, ABBREVIATIONS[t.lower])
                    issues.append(Issue(t.start, t.end, t.text, "Dạng viết tắt không phù hợp văn bản trang trọng.", "ABBREV", "abbrev", "medium", [Suggestion(replacement, "Viết đầy đủ")]))
                    frozen.add(i)
                    handled.add(i)
                elif self._skip(tokens, i, text):
                    frozen.add(i)
                elif capitalization_error(tokens, i, text, self.model, self.config.capitalization_min_count):
                    issues.append(Issue(t.start, t.end, t.text, "Từ thông dụng viết hoa giữa câu; cân nhắc viết thường.", "CAPITALIZATION", "capitalization", "medium", [Suggestion(t.text[:1].lower()+t.text[1:])], LEGAL_CAPITALIZATION))
                    frozen.add(i)
                    handled.add(i)
            for i, replacement, delta in self.restorer.restore(words, frozen):
                t = tokens[i]
                issues.append(Issue(t.start, t.end, t.text, "Có thể thiếu dấu theo ngữ cảnh cả câu.", "DIACRITIC", "diacritic", "medium", [Suggestion(match_case(t.text, replacement), "Khôi phục dấu", delta)]))
                handled.add(i)
            for i, t in enumerate(tokens):
                if i in frozen or i in handled:
                    continue
                word = t.lower
                unknown = word not in self.model.lexicon
                demo_valid_unknown = unknown and self.model.meta.get("quality") == "demo" and word in generate_syllables()
                cheap = self.generator.cheap(word)
                scored = [(self._delta(words, i, w), w, reason, "CONFUSION") for w, reason in cheap.items()]
                # Unknown syllables or improbable context open the expensive search gate.
                gated = unknown or self.model.logprob(words[max(0, i-2):i], word) < self.config.context_threshold
                if gated and not demo_valid_unknown:
                    scored.extend((self._delta(words, i, w)-SECOND_EDIT_PENALTY*max(0, damerau_levenshtein(word, w)-1), w, r, "FUZZY" if unknown else "CONTEXT") for w, r in self.generator.fuzzy(word).items() if w not in cheap
                        and not (not unknown and strip_tone(w) == strip_tone(word) and get_tone(w) == get_tone(word)))
                accepted = [(d, w, r, k) for d, w, r, k in scored if d >= (self.config.min_delta_confusion if k == "CONFUSION" else self.config.min_delta_fuzzy)]
                accepted.sort(key=lambda c: (-c[0], c[1]))
                if accepted:
                    d, w, reason, kind = accepted[0]
                    issues.append(Issue(t.start, t.end, t.text, reason+"; gợi ý dựa trên ngữ cảnh.", kind, kind.lower(), "medium", [Suggestion(match_case(t.text, a), r, s) for s, a, r, _ in accepted[:5]]))
                elif unknown and self.model.meta.get("quality") != "demo":
                    issues.append(Issue(t.start, t.end, t.text, "Âm tiết chưa có trong từ điển; có thể là tên riêng hoặc từ chuyên ngành.", "UNKNOWN", "unknown", "low"))
        # A sentence-initial missing accent and capital letter are one edit.
        starts = {i.start: i for i in issues if i.rule_id == "LOWERCASE_SENTENCE_START"}
        for issue in issues:
            if issue.rule_id == "DIACRITIC" and issue.start in starts:
                issue.suggestions = [Suggestion(s.text[:1].upper()+s.text[1:], s.reason, s.score) for s in issue.suggestions]
        issues = [i for i in issues if i.rule_id != "LOWERCASE_SENTENCE_START" or not any(j.rule_id == "DIACRITIC" and j.start == i.start for j in issues)]
        return CheckResult(text, resolve_overlaps(issues))
