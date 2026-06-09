from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.data_collection.collector import collection_stats
from scripts.data_collection.schema import COLLECTION_COLUMNS, validate_row


def repo_root() -> Path:
    return _REPO


def merge_sources(
    *,
    sources: list[Path],
    out_path: Path,
    source_tag: bool = True,
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for src in sources:
        if not src.exists():
            raise FileNotFoundError(f"Missing source file: {src}")
        df = pd.read_csv(src)
        for col in COLLECTION_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        rows = []
        for i, raw in enumerate(df.to_dict(orient="records"), start=1):
            row = validate_row(raw, row_index=i)
            if source_tag:
                tag = src.stem
                if row["feature_notes"]:
                    row["feature_notes"] = f"{row['feature_notes']};source={tag}"
                else:
                    row["feature_notes"] = f"source={tag}"
            rows.append(row)
        frames.append(pd.DataFrame(rows))

    merged = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=list(COLLECTION_COLUMNS))

    # One row per unique message; smishing label wins conflicts.
    merged["label_rank"] = merged["label"].map({"benign": 0, "smishing": 1}).astype(int)
    merged = (
        merged.sort_values("label_rank")
        .groupby("message", as_index=False)
        .agg(
            label=("label", "last"),
            feature_notes=("feature_notes", "last"),
        )
    )
    merged = merged[list(COLLECTION_COLUMNS)]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(out_path, index=False)
    return merged


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Merge collected + public CSVs into one Dataset1.csv file."
    )
    parser.add_argument(
        "--collected",
        default=str(repo_root() / "data" / "raw" / "collected_sms.csv"),
        help="Manual collection CSV (default: data/raw/collected_sms.csv)",
    )
    parser.add_argument(
        "--uci-collected",
        default=str(repo_root() / "data" / "raw" / "uci_as_collected.csv"),
        help="UCI converted CSV (from download_datasets.py --uci-to-collected)",
    )
    parser.add_argument(
        "--existing",
        default=str(repo_root() / "ml-backend" / "dataset" / "Dataset1.csv"),
        help="Existing Dataset1.csv to include in merge",
    )
    parser.add_argument(
        "--out",
        default=str(repo_root() / "ml-backend" / "dataset" / "Dataset1.csv"),
        help="Merged output path",
    )
    parser.add_argument(
        "--only-collected",
        action="store_true",
        help="Merge only --collected (skip UCI and existing Dataset1)",
    )
    parser.add_argument(
        "--include-uci",
        action="store_true",
        help="Include UCI converted file if it exists",
    )
    parser.add_argument(
        "--include-existing",
        action="store_true",
        help="Include existing Dataset1.csv in the merge",
    )
    args = parser.parse_args(argv)

    sources: list[Path] = []
    collected = Path(args.collected)
    if collected.exists():
        sources.append(collected)
    elif not args.only_collected:
        print(f"Note: collected file not found ({collected})")

    if args.only_collected:
        if not collected.exists():
            raise FileNotFoundError(f"--only-collected set but file missing: {collected}")
    else:
        if args.include_uci:
            uci = Path(args.uci_collected)
            if uci.exists():
                sources.append(uci)
            else:
                print(f"Note: UCI collected file not found ({uci})")
        if args.include_existing:
            existing = Path(args.existing)
            if existing.exists():
                sources.append(existing)
            else:
                print(f"Note: existing Dataset1 not found ({existing})")

    if not sources:
        raise ValueError("No input files to merge. Collect samples first or pass --include-uci / --include-existing.")

    merged = merge_sources(sources=sources, out_path=Path(args.out))
    stats = collection_stats(merged)
    print(f"Wrote {stats['rows']} rows ({stats['unique_messages']} unique messages) -> {args.out}")
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
