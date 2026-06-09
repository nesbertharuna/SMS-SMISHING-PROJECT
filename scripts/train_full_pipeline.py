from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Optional


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _python() -> list[str]:
    """Use the same interpreter that's running this script (works with activated venv)."""
    return [sys.executable]


def _run(cwd: Path, argv: list[str]) -> None:
    print("\n>", " ".join(argv), flush=True)
    subprocess.run(argv, cwd=cwd, check=True)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "End-to-end training: normalize data → stratified splits → train TF-IDF+LogReg → evaluate on test. "
            "Run from repo root recommended; script sets cwd to repo root automatically."
        )
    )
    parser.add_argument(
        "--dataset",
        choices=("dataset1", "uci"),
        required=True,
        help="dataset1: benign/smishing CSV (like Dataset1). uci: UCI SMSSpamCollection tab file.",
    )
    parser.add_argument(
        "--input",
        dest="input_path",
        default=None,
        help=(
            "Path to raw data. Overrides defaults: dataset1→ml-backend/dataset/Dataset1.csv, "
            "uci→data/raw/SMSSpamCollection."
        ),
    )
    parser.add_argument(
        "--processed-out",
        default=None,
        help=(
            "Where to write normalized CSV (default: data/processed/dataset1.csv or data/processed/uci_sms.csv)."
        ),
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for stratified splits (default 42).")
    parser.add_argument(
        "--artifact",
        default=str(Path("ml-backend") / "artifacts" / "pipeline_lr_tfidf.joblib"),
        help="Saved model path relative to repo (default ml-backend/artifacts/pipeline_lr_tfidf.joblib).",
    )
    parser.add_argument("--no-eval", action="store_true", help="Skip ML evaluation on test.csv.")
    parser.add_argument(
        "--eval-overwrite",
        action="store_true",
        help=(
            "Pass --overwrite to evaluate_ml.py (fixed reports/metrics_ml_test.json and "
            "reports/pred_ml_test.csv). Default evaluates to timestamped files."
        ),
    )
    args = parser.parse_args(argv)

    repo = _repo_root()
    py = _python()

    if args.dataset == "dataset1":
        raw_default = repo / "ml-backend" / "dataset" / "Dataset1.csv"
        in_path = Path(args.input_path) if args.input_path else raw_default
        processed = (
            Path(args.processed_out)
            if args.processed_out
            else repo / "data" / "processed" / "dataset1.csv"
        )
        load_script = repo / "scripts" / "load_dataset1.py"
        _run(repo, [*py, str(load_script), "--in", str(in_path), "--out", str(processed)])
    else:
        raw_default = repo / "data" / "raw" / "SMSSpamCollection"
        in_path = Path(args.input_path) if args.input_path else raw_default
        processed = (
            Path(args.processed_out)
            if args.processed_out
            else repo / "data" / "processed" / "uci_sms.csv"
        )
        load_script = repo / "scripts" / "load_uci_sms.py"
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

    train_py = repo / "experiments" / "train.py"
    train_csv = splits_dir / "train.csv"
    val_csv = splits_dir / "val.csv"
    _run(
        repo,
        [
            *py,
            str(train_py),
            "--train",
            str(train_csv.relative_to(repo)),
            "--val",
            str(val_csv.relative_to(repo)),
            "--artifact",
            args.artifact,
            "--seed",
            str(args.seed),
        ],
    )

    if not args.no_eval:
        eval_py = repo / "experiments" / "evaluate_ml.py"
        test_csv = splits_dir / "test.csv"
        eval_argv = [
            *py,
            str(eval_py),
            "--test",
            str(test_csv.relative_to(repo)),
            "--artifact",
            args.artifact,
        ]
        if args.eval_overwrite:
            eval_argv.append("--overwrite")
        _run(repo, eval_argv)

    print("\nDone.")
    print(f"  Processed: {processed}")
    print(f"  Splits:    {splits_dir}")
    print(f"  Model:     {repo / Path(args.artifact)}")
    if not args.no_eval:
        if args.eval_overwrite:
            print(f"  Metrics:   {repo / 'reports' / 'metrics_ml_test.json'} (overwrite)")
        else:
            print(f"  Metrics:   {repo / 'reports' / 'metrics_ml_test_<UTC_timestamp>.json'} (see evaluate output above)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
