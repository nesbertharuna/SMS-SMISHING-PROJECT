from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

import pandas as pd


def load_dissertation(path: str | Path) -> pd.DataFrame:
    """
    Load the dissertation Excel/CSV dataset and normalize to modelling schema.

    Expected columns (case-insensitive):
      - LABEL or label: 'benign' / 'smishing'
      - TEXT or message: SMS text

    Returns DataFrame with columns: label (0/1), message, source.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Missing file: {p}")

    if p.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(p)
    else:
        df = pd.read_csv(p)

    cols = {c.lower(): c for c in df.columns}
    label_col = cols.get("label")
    text_col = cols.get("text") or cols.get("message")
    if label_col is None or text_col is None:
        raise ValueError("Expected columns LABEL/label and TEXT/message")

    out = pd.DataFrame()
    out["message"] = df[text_col].astype(str)
    raw_labels = df[label_col]

    if pd.api.types.is_numeric_dtype(raw_labels):
        out["label"] = raw_labels.astype(int)
    else:
        out["label_raw"] = raw_labels.astype(str).str.strip().str.lower()
        label_map = {"benign": 0, "smishing": 1, "0": 0, "1": 1}
        unknown = sorted(set(out["label_raw"].unique()) - set(label_map.keys()))
        if unknown:
            raise ValueError(f"Unknown labels: {unknown}")
        out["label"] = out["label_raw"].map(label_map).astype(int)
    out["source"] = "dissertation"
    out = out.dropna(subset=["message", "label"]).copy()

    out = (
        out.groupby("message", as_index=False)
        .agg(label=("label", "max"), source=("source", "first"))
        .reset_index(drop=True)
    )
    return out[["label", "message", "source"]]


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Load dissertation dataset into normalized CSV.")
    parser.add_argument(
        "--in",
        dest="in_path",
        default=str(Path("data") / "processed" / "Dataset for dissertation.csv.xlsx"),
        help="Input .xlsx or .csv path",
    )
    parser.add_argument(
        "--out",
        dest="out_path",
        default=str(Path("data") / "processed" / "dissertation.csv"),
        help="Output CSV path (default: data/processed/dissertation.csv)",
    )
    args = parser.parse_args(argv)

    out_path = Path(args.out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    df = load_dissertation(args.in_path)
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df)} rows -> {out_path}")
    print(df["label"].value_counts(dropna=False).sort_index().rename(index={0: "benign(0)", 1: "smishing(1)"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
