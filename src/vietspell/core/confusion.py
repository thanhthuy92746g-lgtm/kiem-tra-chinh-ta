from .normalize import get_tone, strip_tone

PREFIX_GROUPS = (("s", "x"), ("ch", "tr"), ("d", "gi", "r"), ("l", "n"), ("v", "d"))
OCR = (("0", "o"), ("1", "l"), ("rn", "m"))
KEY_ROWS = ("qwertyuiop", "asdfghjkl", "zxcvbnm")


def confusion_forms(word):
    forms = {}
    for group in PREFIX_GROUPS:
        for prefix in group:
            if word.startswith(prefix):
                for other in group:
                    if prefix != other:
                        forms[other + word[len(prefix):]] = "Nhầm phụ âm đầu/phương ngữ"
    for a, b in OCR + (("i", "y"),):
        if a in word:
            forms[word.replace(a, b)] = "Biến thể ký tự/OCR"
        if b in word:
            forms[word.replace(b, a)] = "Biến thể ký tự/OCR"
    for row in KEY_ROWS:
        for i, c in enumerate(word):
            if c in row:
                p = row.index(c)
                for n in row[max(0, p-1):p+2]:
                    if n != c:
                        forms[word[:i]+n+word[i+1:]] = "Phím liền kề"
    return forms
