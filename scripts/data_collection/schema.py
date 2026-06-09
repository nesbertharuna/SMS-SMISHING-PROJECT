from __future__ import annotations

from typing import Any, Dict

VALID_LABELS = frozenset({"benign", "smishing"})
COLLECTION_COLUMNS = ("label", "message", "feature_notes")

# Common feature_notes tags used in this project (documentation only — not enforced).
FEATURE_NOTE_EXAMPLES = (
    "urgency",
    "malicious_url",
    "impersonation",
    "credential_request",
    "financial_lure",
    "obfuscation",
    "banking_notification",
    "otp_notification",
    "personal_message",
    "reminder",
)


def normalize_label(label: Any) -> str:
    value = str(label).strip().lower()
    if value in {"0", "ham", "safe", "legit", "legitimate"}:
        return "benign"
    if value in {"1", "spam", "phish", "phishing", "smish", "malicious"}:
        return "smishing"
    if value not in VALID_LABELS:
        raise ValueError(f"Invalid label {label!r}. Use one of: {sorted(VALID_LABELS)}")
    return value


def validate_row(row: Dict[str, Any], *, row_index: int | None = None) -> Dict[str, str]:
    prefix = f"Row {row_index}: " if row_index is not None else ""
    if "message" not in row:
        raise ValueError(f"{prefix}missing required column 'message'")

    message = str(row["message"]).strip()
    if not message:
        raise ValueError(f"{prefix}message must not be empty")

    if "label" not in row:
        raise ValueError(f"{prefix}missing required column 'label'")

    label = normalize_label(row["label"])
    feature_notes = str(row.get("feature_notes", "")).strip()
    return {
        "label": label,
        "message": message,
        "feature_notes": feature_notes,
    }
