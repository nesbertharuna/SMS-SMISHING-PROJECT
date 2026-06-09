from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

import pandas as pd


def load_uci_sms(path: str | Path) -> pd.DataFrame:
    """
    Load the UCI SMS Spam Collection file (usually named 'SMSSpamCollection').

    Expected format (no header, tab-separated):
      label<TAB>message
    where label is 'ham' or 'spam'.

    Returns a DataFrame with:
      - label: int (0=ham/benign, 1=spam/malicious)
      - message: str
      - source: str ('uci')
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Missing file: {p}")

    df = pd.read_csv(p, sep="\t", header=None, names=["label_raw", "message"], encoding_errors="replace")
    df["message"] = df["message"].astype(str)
    df["label_raw"] = df["label_raw"].astype(str).str.strip().str.lower()

    label_map = {"ham": 0, "spam": 1}
    unknown = sorted(set(df["label_raw"].unique()) - set(label_map.keys()))
    if unknown:
        raise ValueError(f"Unknown labels in UCI file: {unknown}")

    df["label"] = df["label_raw"].map(label_map).astype(int)
    df["source"] = "uci"

    # Basic cleanup
    df = df.dropna(subset=["message", "label"]).copy()
    df = df.drop_duplicates(subset=["label", "message"]).reset_index(drop=True)
    return df[["label", "message", "source"]]


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Load UCI SMS Spam Collection into a normalized CSV.")
    parser.add_argument(
        "--in",
        dest="in_path",
        default=str(Path("data") / "raw" / "SMSSpamCollection"),
        help="Path to SMSSpamCollection (default: data/raw/SMSSpamCollection)",
    )
    parser.add_argument(
        "--out",
        dest="out_path",
        default=str(Path("data") / "processed" / "uci_sms.csv"),
        help="Output CSV path (default: data/processed/uci_sms.csv)",
    )

    args = parser.parse_args(argv)
    out_path = Path(args.out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    df = load_uci_sms(args.in_path)
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df)} rows -> {out_path}")
    print(df["label"].value_counts(dropna=False).sort_index().rename(index={0: "ham(0)", 1: "spam(1)"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

