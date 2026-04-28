import re
from typing import Iterable, List, Optional, Sequence, Set


# Small, dependency-free English stopword list (customize as needed).
DEFAULT_STOPWORDS: Set[str] = {
    "a",
    "about",
    "above",
    "after",
    "again",
    "against",
    "all",
    "am",
    "an",
    "and",
    "any",
    "are",
    "as",
    "at",
    "be",
    "because",
    "been",
    "before",
    "being",
    "below",
    "between",
    "both",
    "but",
    "by",
    "can",
    "could",
    "did",
    "do",
    "does",
    "doing",
    "down",
    "during",
    "each",
    "few",
    "for",
    "from",
    "further",
    "had",
    "has",
    "have",
    "having",
    "he",
    "her",
    "here",
    "hers",
    "herself",
    "him",
    "himself",
    "his",
    "how",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "itself",
    "just",
    "me",
    "more",
    "most",
    "my",
    "myself",
    "no",
    "nor",
    "not",
    "now",
    "of",
    "off",
    "on",
    "once",
    "only",
    "or",
    "other",
    "our",
    "ours",
    "ourselves",
    "out",
    "over",
    "own",
    "s",
    "same",
    "she",
    "should",
    "so",
    "some",
    "such",
    "t",
    "than",
    "that",
    "the",
    "their",
    "theirs",
    "them",
    "themselves",
    "then",
    "there",
    "these",
    "they",
    "this",
    "those",
    "through",
    "to",
    "too",
    "under",
    "until",
    "up",
    "very",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "which",
    "while",
    "who",
    "whom",
    "why",
    "will",
    "with",
    "you",
    "your",
    "yours",
    "yourself",
    "yourselves",
}


_PUNCT_RE = re.compile(r"[^\w\s]+", flags=re.UNICODE)
_WS_RE = re.compile(r"\s+", flags=re.UNICODE)


def preprocess_sms(
    text: str,
    *,
    stopwords: Optional[Iterable[str]] = None,
    keep_numbers: bool = True,
) -> List[str]:
    """
    Preprocess SMS text:
    - lowercase
    - remove punctuation
    - remove stopwords
    - tokenize
    """
    if text is None:
        return []

    normalized = text.lower()
    normalized = _PUNCT_RE.sub(" ", normalized)  # remove punctuation/symbols
    normalized = _WS_RE.sub(" ", normalized).strip()

    tokens = normalized.split(" ") if normalized else []

    sw = set(stopwords) if stopwords is not None else DEFAULT_STOPWORDS
    out: List[str] = []
    for tok in tokens:
        if not tok:
            continue
        if not keep_numbers and tok.isdigit():
            continue
        if tok in sw:
            continue
        out.append(tok)
    return out


def preprocess_sms_to_string(
    text: str,
    *,
    stopwords: Optional[Sequence[str]] = None,
    keep_numbers: bool = True,
) -> str:
    """Same as `preprocess_sms`, but returns a space-joined string."""
    return " ".join(preprocess_sms(text, stopwords=stopwords, keep_numbers=keep_numbers))

