from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

import pandas as pd


def load_dataset1(path: str | Path) -> pd.DataFrame:
    """
    Load `ml-backend/dataset/Dataset1.csv` and normalize to the project's schema.

    Expected columns:
      - label: 'smishing' or 'benign' (case-insensitive)
      - message: SMS text
      - feature_notes: optional (ignored for training)

    Returns a DataFrame with:
      - label: int (0=benign, 1=smishing)
      - message: str
      - source: str ('dataset1')
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Missing file: {p}")

    df = pd.read_csv(p)
    if not {"label", "message"}.issubset(df.columns):
        raise ValueError("Expected CSV columns to include: label, message")

    df["message"] = df["message"].astype(str)
    df["label_raw"] = df["label"].astype(str).str.strip().str.lower()

    label_map = {"benign": 0, "smishing": 1}
    unknown = sorted(set(df["label_raw"].unique()) - set(label_map.keys()))
    if unknown:
        raise ValueError(f"Unknown labels in Dataset1.csv: {unknown}")

    df["label"] = df["label_raw"].map(label_map).astype(int)
    df["source"] = "dataset1"

    # Basic cleanup
    df = df.dropna(subset=["message", "label"]).copy()

    # Deduplicate by message only. If a message appears with multiple labels,
    # treat it as smishing if any row is labeled smishing.
    df = (
        df.groupby("message", as_index=False)
        .agg(
            label=("label", "max"),
            source=("source", "first"),
        )
        .reset_index(drop=True)
    )
    unique_messages = len(df)
    if unique_messages < 50:
        print(
            f"WARNING: Only {unique_messages} unique messages after normalization. "
            "ML metrics will be unstable on tiny datasets. "
            "Consider using the UCI SMS dataset (`--dataset uci`) for evaluation."
        )
    return df[["label", "message", "source"]]


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Load Dataset1.csv into a normalized CSV (label=0/1).")
    parser.add_argument(
        "--in",
        dest="in_path",
        default=str(Path("ml-backend") / "dataset" / "Dataset1.csv"),
        help="Path to Dataset1.csv (default: ml-backend/dataset/Dataset1.csv)",
    )
    parser.add_argument(
        "--out",
        dest="out_path",
        default=str(Path("data") / "processed" / "dataset1.csv"),
        help="Output CSV path (default: data/processed/dataset1.csv)",
    )
    args = parser.parse_args(argv)

    out_path = Path(args.out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    df = load_dataset1(args.in_path)
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df)} rows -> {out_path}")
    print(df["label"].value_counts(dropna=False).sort_index().rename(index={0: "benign(0)", 1: "smishing(1)"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

