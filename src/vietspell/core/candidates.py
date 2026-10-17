from collections import defaultdict
from functools import lru_cache

from .confusion import confusion_forms
from .normalize import get_tone, strip_tone


def damerau_levenshtein(a: str, b: str, limit=2) -> int:
    """Unrestricted Damerau-Levenshtein; return limit+1 for impossible lengths."""
    if abs(len(a)-len(b)) > limit:
        return limit+1
    height, width = len(a), len(b)
    infinity = height+width
    matrix = [[0]*(width+2) for _ in range(height+2)]
    matrix[0][0] = infinity
    for i in range(height+1):
        matrix[i+1][0], matrix[i+1][1] = infinity, i
    for j in range(width+1):
        matrix[0][j+1], matrix[1][j+1] = infinity, j
    last_seen = {}
    for i, ac in enumerate(a, 1):
        last_match = 0
        for j, bc in enumerate(b, 1):
            earlier_i, earlier_j = last_seen.get(bc, 0), last_match
            cost = int(ac != bc)
            if not cost:
                last_match = j
            matrix[i+1][j+1] = min(matrix[i][j]+cost, matrix[i+1][j]+1,
                matrix[i][j+1]+1,
                matrix[earlier_i][earlier_j]+(i-earlier_i-1)+1+(j-earlier_j-1))
        last_seen[ac] = i
    return matrix[height+1][width+1]


class CandidateGenerator:
    def __init__(self, lexicon):
        self.lexicon = lexicon
        self.by_length = defaultdict(list)
        self.by_tone_base = defaultdict(list)
        for w in sorted(lexicon):
            self.by_length[len(w)].append(w)
            self.by_tone_base[strip_tone(w)].append(w)
        self.deletion_index = None
        self.fuzzy = lru_cache(maxsize=4096)(self.fuzzy)

    @staticmethod
    def deletes(word):
        forms = {word}
        frontier = {word}
        for _ in range(2):
            frontier = {value[:i]+value[i+1:] for value in frontier for i in range(len(value))}
            forms.update(frontier)
        return forms

    def cheap(self, word):
        forms = {w: r for w, r in confusion_forms(word).items() if w in self.lexicon}
        if get_tone(word) in {"hoi", "nga"}:
            for w in self.by_tone_base[strip_tone(word)]:
                if {get_tone(word), get_tone(w)} == {"hoi", "nga"}:
                    forms[w] = "Nhầm dấu hỏi/ngã"
        for i in range(1, len(word)):
            if word[:i] in self.lexicon and word[i:] in self.lexicon:
                forms[word[:i] + " " + word[i:]] = "Hai âm tiết bị dính"
        return forms

    def fuzzy(self, word):
        if not self.by_length or len(word) > max(self.by_length)+2:
            return {}
        if self.deletion_index is None:
            self.deletion_index = defaultdict(set)
            for value in self.lexicon:
                for key in self.deletes(value):
                    self.deletion_index[key].add(value)
        possible = set()
        for key in self.deletes(word):
            possible.update(self.deletion_index.get(key, ()))
        result = {}
        for w in sorted(possible):
            if w != word and abs(len(w)-len(word)) <= 2 and damerau_levenshtein(word, w) <= 2:
                result[w] = "Gần giống ký tự"
        return result
