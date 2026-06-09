from __future__ import annotations

"""
Rule-based baseline only — load data, split, evaluate on test set.
No ML training or inference.
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Optional


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _python() -> list[str]:
    return [sys.executable]


def _run(cwd: Path, argv: list[str]) -> None:
    print("\n>", " ".join(argv), flush=True)
    subprocess.run(argv, cwd=cwd, check=True)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate rule-based smishing baseline on test split (no ML)."
    )
    parser.add_argument(
        "--input",
        dest="input_path",
        default=str(Path("data") / "processed" / "Dataset for dissertation.csv.xlsx"),
        help="Dissertation .xlsx/.csv path",
    )
    parser.add_argument(
        "--processed-out",
        default=str(Path("data") / "processed" / "dissertation.csv"),
        help="Normalized CSV output (default: data/processed/dissertation.csv)",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for splits (default 42)")
    parser.add_argument(
        "--threshold",
        type=int,
        default=6,
        help="Rule score threshold (default 6)",
    )
    parser.add_argument(
        "--metrics-out",
        default=str(Path("reports") / "metrics_rules_baseline.json"),
        help="Metrics JSON path (default: reports/metrics_rules_baseline.json)",
    )
    parser.add_argument(
        "--pred-out",
        default=str(Path("reports") / "pred_rules_baseline.csv"),
        help="Predictions CSV path (default: reports/pred_rules_baseline.csv)",
    )
    args = parser.parse_args(argv)

    repo = _repo_root()
    py = _python()
    in_path = Path(args.input_path)
    if not in_path.is_absolute():
        in_path = repo / in_path
    processed = repo / Path(args.processed_out)

    load_script = repo / "scripts" / "load_dissertation.py"
    _run(repo, [*py, str(load_script), "--in", str(in_path), "--out", str(processed)])

    splits_dir = repo / "data" / "splits"
    make_splits = repo / "scripts" / "make_splits.py"
    _run(
        repo,
        [
            *py,
            str(make_splits),
            "--in",
            str(processed),
            "--out_dir",
            str(splits_dir),
            "--seed",
            str(args.seed),
        ],
    )

    baseline = repo / "ml-backend" / "rule-engine" / "rule_based_baseline.py"
    test_csv = splits_dir / "test.csv"
    _run(
        repo,
        [
            *py,
            str(baseline),
            "--test",
            str(test_csv.relative_to(repo)),
            "--threshold",
            str(args.threshold),
            "--out",
            args.metrics_out,
            "--pred_out",
            args.pred_out,
        ],
    )

    print("\nDone — rule-based baseline metrics only (no ML).")
    print(f"  Processed: {processed}")
    print(f"  Test set:  {test_csv}")
    print(f"  Metrics:   {repo / Path(args.metrics_out)}")
    print(f"  Predictions: {repo / Path(args.pred_out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
