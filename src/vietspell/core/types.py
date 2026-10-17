from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class Suggestion:
    text: str
    reason: str = ""
    score: float = 0.0


@dataclass
class Issue:
    start: int
    end: int
    text: str
    message: str
    rule_id: str
    kind: str = "format"
    severity: str = "low"
    suggestions: list[Suggestion] = field(default_factory=list)
    basis: str = "Gợi ý ngôn ngữ — cần kiểm tra theo ngữ cảnh."
    confidence: str = "high"
    occurrences: int = 1

    @property
    def editable(self) -> bool:
        return bool(self.suggestions)

    def to_dict(self):
        return asdict(self)


@dataclass
class CheckResult:
    text: str
    issues: list[Issue]
    warnings: list[str] = field(default_factory=list)

    def to_dict(self):
        return {"issues": [i.to_dict() for i in self.issues], "warnings": self.warnings}


def resolve_overlaps(issues: list[Issue]) -> list[Issue]:
    """Specific replacements win; descriptive document findings remain separate."""
    priority = {"SPACE_BEFORE_PUNCT": 0, "SPACE_INSIDE_BRACKET": 0,
                "TRAILING_SPACE": 1, "LEADING_SPACE": 1, "SPACE_MULTI": 5}
    kept = []
    for issue in sorted(issues, key=lambda i: (priority.get(i.rule_id, 2), i.start, -(i.end-i.start))):
        if issue.editable and any(k.editable and issue.start < k.end and k.start < issue.end for k in kept):
            continue
        kept.append(issue)
    return sorted(kept, key=lambda i: (i.start, i.end, i.rule_id))
