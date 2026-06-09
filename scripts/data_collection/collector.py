from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd

from .schema import COLLECTION_COLUMNS, validate_row


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_collection_path() -> Path:
    return repo_root() / "data" / "raw" / "collected_sms.csv"


def collection_stats(df: pd.DataFrame) -> Dict[str, Any]:
    if df.empty:
        return {
            "rows": 0,
            "unique_messages": 0,
            "benign": 0,
            "smishing": 0,
            "label_conflicts": 0,
        }

    work = df.copy()
    work["label"] = work["label"].astype(str).str.strip().str.lower()
    work["message"] = work["message"].astype(str)

    conflicts = (
        work.groupby("message")["label"]
        .nunique()
        .gt(1)
        .sum()
    )
    benign = int((work["label"] == "benign").sum())
    smishing = int((work["label"] == "smishing").sum())
    return {
        "rows": len(work),
        "unique_messages": int(work["message"].nunique()),
        "benign": benign,
        "smishing": smishing,
        "label_conflicts": int(conflicts),
    }


class SmsCollector:
    """
    Append-only store for manually collected SMS samples.

    CSV schema (Dataset1-compatible):
      - label: benign | smishing
      - message: SMS text
      - feature_notes: optional tags (e.g. urgency, malicious_url)
    """

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else default_collection_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> pd.DataFrame:
        if not self.path.exists():
            return pd.DataFrame(columns=list(COLLECTION_COLUMNS))
        df = pd.read_csv(self.path)
        for col in COLLECTION_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df[list(COLLECTION_COLUMNS)].fillna("")

    def save(self, df: pd.DataFrame) -> None:
        out = df[list(COLLECTION_COLUMNS)].copy()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        out.to_csv(self.path, index=False)

    def add_sample(self, *, label: str, message: str, feature_notes: str = "") -> Dict[str, str]:
        row = validate_row({"label": label, "message": message, "feature_notes": feature_notes})
        df = self.load()
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        self.save(df)
        return row

    def add_rows(self, rows: Iterable[Dict[str, Any]]) -> int:
        normalized: List[Dict[str, str]] = []
        for i, raw in enumerate(rows, start=1):
            normalized.append(validate_row(raw, row_index=i))
        if not normalized:
            return 0
        df = self.load()
        df = pd.concat([df, pd.DataFrame(normalized)], ignore_index=True)
        self.save(df)
        return len(normalized)

    def add_from_csv(self, csv_path: str | Path) -> int:
        incoming = pd.read_csv(csv_path)
        rows = incoming.to_dict(orient="records")
        return self.add_rows(rows)

    def add_from_jsonl(self, jsonl_path: str | Path) -> int:
        rows: List[Dict[str, Any]] = []
        text = Path(jsonl_path).read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(text, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {i} of {jsonl_path}") from exc
        return self.add_rows(rows)

    def dedupe(self, *, keep: str = "last") -> int:
        """
        Remove exact duplicate rows (label + message + feature_notes).
        Returns number of rows removed.
        """
        df = self.load()
        before = len(df)
        df = df.drop_duplicates(subset=list(COLLECTION_COLUMNS), keep=keep).reset_index(drop=True)
        removed = before - len(df)
        if removed:
            self.save(df)
        return removed

    def export_dataset1(self, out_path: str | Path, *, dedupe_messages: bool = True) -> Path:
        """
        Export to Dataset1.csv format at `out_path`.
        When dedupe_messages=True, one row per unique message (smishing wins ties).
        """
        df = self.load().copy()
        if df.empty:
            raise ValueError("No collected samples to export.")

        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        if dedupe_messages:
            df["label_rank"] = df["label"].map({"benign": 0, "smishing": 1}).fillna(0).astype(int)
            df = (
                df.sort_values("label_rank")
                .groupby("message", as_index=False)
                .agg(
                    label=("label", "last"),
                    feature_notes=("feature_notes", "last"),
                )
                .drop(columns=[], errors="ignore")
            )

        df = df[list(COLLECTION_COLUMNS)]
        df.to_csv(out, index=False)
        return out

    def write_audit_log(self, action: str, details: Dict[str, Any]) -> Path:
        log_path = self.path.with_suffix(".log.jsonl")
        entry = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "collection_file": str(self.path),
            **details,
        }
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return log_path
