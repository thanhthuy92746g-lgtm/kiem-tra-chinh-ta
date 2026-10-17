from collections import defaultdict

from .normalize import fold_diacritics, get_tone

MAX_VARIANTS = 12
MIN_FREQUENCY_SHARE = 0.5
UNKNOWN_SCORE = -6.0
RARE_UNIGRAM = 200


def is_restorable(word):
    return get_tone(word) == "ngang"


class DiacriticRestorer:
    def __init__(self, model, beam_width=8, min_delta=1.0, min_delta_run=1.0):
        self.model = model
        self.beam_width = beam_width
        self.min_delta, self.min_delta_run = min_delta, min_delta_run
        self.groups = defaultdict(list)
        for w in model.lexicon:
            self.groups[fold_diacritics(w)].append(w)

    def variants(self, word):
        if not is_restorable(word):
            return [word]
        count = self.model.c1(word)
        choices = [w for w in self.groups[fold_diacritics(word)] if self.model.c1(w) >= MIN_FREQUENCY_SHARE * count]
        choices.sort(key=lambda w: (-self.model.c1(w), w))
        return [word] + [w for w in choices if w != word][:MAX_VARIANTS-1]

    def score(self, words, start=0, end=None):
        end = len(words) if end is None else min(end, len(words))
        return sum(self.model.logprob(words[max(0, i-2):i], words[i]) if words[i] in self.model.lexicon else UNKNOWN_SCORE for i in range(start, end))

    def restore(self, words, frozen=frozenset()):
        beam = [(0.0, [])]
        for i, word in enumerate(words):
            expanded = []
            for score, history in beam:
                for w in [word] if i in frozen else self.variants(word):
                    s = self.model.logprob(history[-2:], w) if w in self.model.lexicon else UNKNOWN_SCORE
                    expanded.append((score+s, history+[w]))
            unique = {}
            for item in sorted(expanded, key=lambda b: (-b[0], b[1])):
                unique.setdefault(tuple(item[1][-2:]), item)
            beam = list(unique.values())[:self.beam_width]
        if not beam:
            return []
        return self._diff(words, beam[0][1])

    def _diff(self, old, new):
        changes, i = [], 0
        while i < len(old):
            if old[i] == new[i]:
                i += 1
                continue
            start = i
            while i < len(old) and old[i] != new[i]:
                i += 1
            n = i-start
            rare = any(self.model.c1(w) < RARE_UNIGRAM for w in old[start:i])
            threshold = self.min_delta*(n-1) if n >= 3 else self.min_delta_run if n == 2 and rare else self.min_delta
            # Score only the window affected by this run, with all other words held fixed.
            trial = old[:start] + new[start:i] + old[i:]
            delta = self.score(trial, start, i+2) - self.score(old, start, i+2)
            if delta >= threshold:
                changes.extend((j, new[j], delta) for j in range(start, i))
        return changes
