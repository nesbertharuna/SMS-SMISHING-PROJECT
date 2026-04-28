from __future__ import annotations

import importlib.util
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


def _load_preprocess_sms():
    """
    Load `preprocess_sms` from `ml-backend/prepocessing/clean_text.py`
    without requiring package (__init__.py) setup.
    """
    backend_root = Path(__file__).resolve().parents[1]  # .../ml-backend
    clean_text_path = backend_root / "prepocessing" / "clean_text.py"

    spec = importlib.util.spec_from_file_location("clean_text", clean_text_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {clean_text_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.preprocess_sms


preprocess_sms = _load_preprocess_sms()


URL_RE = re.compile(
    r"(?i)\b(?:https?://|www\.)\S+|\b[a-z0-9-]+(?:\.[a-z0-9-]+)+/\S+"
)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{6,}\d)(?!\d)")
MONEY_RE = re.compile(r"(?i)(?:[$£€]\s*\d+|\b\d+\s*(?:usd|gbp|eur)\b)")


@dataclass(frozen=True)
class RuleConfig:
    threshold: int = 6
    keyword_weight: int = 2
    url_weight: int = 4
    phone_weight: int = 2
    money_weight: int = 1


DEFAULT_KEYWORDS: Tuple[str, ...] = (
    "urgent",
    "verify",
    "account",
    "password",
    "login",
    "confirm",
    "suspended",
    "locked",
    "security",
    "fraud",
    "unauthorized",
    "reset",
    "update",
    "payment",
    "billing",
    "refund",
    "claim",
    "winner",
    "prize",
    "free",
    "offer",
    "limited",
    "act",
    "now",
)


PHRASES: Tuple[Tuple[str, int, str], ...] = (
    ("verify your account", 3, "phrase:verify your account"),
    ("account suspended", 3, "phrase:account suspended"),
    ("unusual activity", 3, "phrase:unusual activity"),
    ("click here", 2, "phrase:click here"),
)


def detect_smishing(
    text: str,
    *,
    config: Optional[RuleConfig] = None,
    keywords: Sequence[str] = DEFAULT_KEYWORDS,
    stopwords: Optional[Sequence[str]] = None,
) -> Dict[str, object]:
    """
    Rule-based SMS detection using keyword + pattern heuristics.

    Returns:
      {
        "is_suspicious": bool,
        "score": int,
        "reasons": [str, ...],
        "matches": {"keywords": [...], "urls": [...], "phones": [...], "phrases": [...]}
      }
    """
    cfg = config or RuleConfig()
    raw = text or ""
    lowered = raw.lower()

    urls = URL_RE.findall(raw)
    phones = PHONE_RE.findall(raw)
    money = MONEY_RE.findall(raw)

    # Token-aware keyword matching (after light preprocessing).
    tokens = preprocess_sms(raw, stopwords=stopwords)
    token_set = set(tokens)

    kw_matches = sorted({kw for kw in keywords if kw.lower() in token_set})

    phrase_matches: List[str] = []
    score = 0
    reasons: List[str] = []

    if urls:
        score += cfg.url_weight
        reasons.append("contains_url")
    if phones:
        score += cfg.phone_weight
        reasons.append("contains_phone_number")
    if money:
        score += cfg.money_weight
        reasons.append("mentions_money_amount")

    if kw_matches:
        score += cfg.keyword_weight * len(kw_matches)
        reasons.append("contains_risky_keywords")

    for phrase, weight, tag in PHRASES:
        if phrase in lowered:
            phrase_matches.append(tag)
            score += weight

    # Simple urgency cue: exclamation density / all-caps tokens.
    exclamations = raw.count("!")
    if exclamations >= 2:
        score += 1
        reasons.append("high_urgency_punctuation")

    all_caps_tokens = [t for t in raw.split() if len(t) >= 4 and t.isupper()]
    if len(all_caps_tokens) >= 2:
        score += 1
        reasons.append("multiple_all_caps_tokens")

    is_suspicious = score >= cfg.threshold

    return {
        "is_suspicious": is_suspicious,
        "score": score,
        "reasons": sorted(set(reasons)),
        "matches": {
            "keywords": kw_matches,
            "phrases": phrase_matches,
            "urls": urls,
            "phones": phones,
            "money": money,
        },
    }


if __name__ == "__main__":
    examples = [
        "URGENT! Verify your account now: http://bit.ly/xyz",
        "Hey, are you coming home soon?",
        "Your account is suspended. Click here to verify: www.example.com/verify",
    ]
    for msg in examples:
        print(msg)
        print(detect_smishing(msg))
