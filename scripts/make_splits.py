from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
from sklearn.model_selection import train_test_split


def stratified_splits(
    df: pd.DataFrame,
    *,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if abs((train_ratio + val_ratio + test_ratio) - 1.0) > 1e-9:
        raise ValueError("train/val/test ratios must sum to 1.0")
    if "label" not in df.columns or "message" not in df.columns:
        raise ValueError("Input df must contain columns: label, message")

    df = df.dropna(subset=["label", "message"]).copy()
    df["label"] = df["label"].astype(int)
    df["message"] = df["message"].astype(str)

    # First split train vs temp (val+test)
    temp_ratio = val_ratio + test_ratio
    train_df, temp_df = train_test_split(
        df,
        test_size=temp_ratio,
        random_state=random_state,
        stratify=df["label"],
    )

    # Then split temp into val/test
    test_share_of_temp = test_ratio / temp_ratio if temp_ratio > 0 else 0.0
    val_df, test_df = train_test_split(
        temp_df,
        test_size=test_share_of_temp,
        random_state=random_state,
        stratify=temp_df["label"],
    )

    return (
        train_df.reset_index(drop=True),
        val_df.reset_index(drop=True),
        test_df.reset_index(drop=True),
    )


def _print_counts(name: str, df: pd.DataFrame) -> None:
    counts = df["label"].value_counts(dropna=False).sort_index()
    print(f"{name}: n={len(df)} | " + ", ".join([f"label={k}: {v}" for k, v in counts.items()]))


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Create stratified train/val/test splits for SMS data.")
    parser.add_argument(
        "--in",
        dest="in_path",
        default=str(Path("data") / "processed" / "uci_sms.csv"),
        help="Input CSV path (default: data/processed/uci_sms.csv)",
    )
    parser.add_argument(
        "--out_dir",
        default=str(Path("data") / "splits"),
        help="Output directory (default: data/splits/)",
    )
    parser.add_argument("--train", type=float, default=0.70, help="Train ratio (default 0.70)")
    parser.add_argument("--val", type=float, default=0.15, help="Validation ratio (default 0.15)")
    parser.add_argument("--test", type=float, default=0.15, help="Test ratio (default 0.15)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default 42)")
    args = parser.parse_args(argv)

    in_path = Path(args.in_path)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(in_path)
    train_df, val_df, test_df = stratified_splits(
        df,
        train_ratio=args.train,
        val_ratio=args.val,
        test_ratio=args.test,
        random_state=args.seed,
    )

    train_path = out_dir / "train.csv"
    val_path = out_dir / "val.csv"
    test_path = out_dir / "test.csv"

    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)

    _print_counts("train", train_df)
    _print_counts("val", val_df)
    _print_counts("test", test_df)
    print(f"Wrote splits -> {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

