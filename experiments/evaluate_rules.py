from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix

try:
    from experiments._load_modules import load_rules_module, repo_root
except ModuleNotFoundError:
    from _load_modules import load_rules_module, repo_root


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate rule baseline on test.csv.")
    parser.add_argument(
        "--test",
        dest="test_csv",
        default=str(Path("data") / "splits" / "test.csv"),
        help="Path to test.csv (default: data/splits/test.csv)",
    )
    parser.add_argument(
        "--out",
        dest="out_json",
        default=str(Path("reports") / "metrics_rules_test.json"),
        help="Where to write metrics JSON (default: reports/metrics_rules_test.json)",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=6,
        help="Rule score threshold (default 6; matches RuleConfig.threshold default)",
    )
    parser.add_argument(
        "--pred_out",
        dest="pred_out_csv",
        default=str(Path("reports") / "pred_rules_test.csv"),
        help="Where to write per-row predictions (default: reports/pred_rules_test.csv)",
    )
    args = parser.parse_args(argv)

    test_df = pd.read_csv(Path(args.test_csv))
    if not {"label", "message"}.issubset(test_df.columns):
        raise ValueError("Expected CSV columns: label, message")

    y_true = test_df["label"].astype(int).tolist()
    messages = test_df["message"].astype(str).tolist()

    rules = load_rules_module()
    cfg = rules.RuleConfig(threshold=args.threshold)

    y_pred = []
    for msg in messages:
        res = rules.detect_smishing(msg, config=cfg)
        y_pred.append(1 if bool(res["is_suspicious"]) else 0)

    report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist()

    out_path = repo_root() / Path(args.out_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    pred_out_path = repo_root() / Path(args.pred_out_csv)
    pred_out_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"y_true": y_true, "y_pred": list(map(int, y_pred))}).to_csv(pred_out_path, index=False)

    payload = {
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "test_csv": str(Path(args.test_csv)),
        "n_test": len(messages),
        "rule_threshold": args.threshold,
        "predictions_csv": str(pred_out_path),
        "confusion_matrix_labels_[0,1]": cm,
        "metrics_pos1": {
            "accuracy": report.get("accuracy"),
            "precision": report.get("1", {}).get("precision"),
            "recall": report.get("1", {}).get("recall"),
            "f1": report.get("1", {}).get("f1-score"),
        },
        "classification_report": report,
    }

    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("Rules test metrics (pos_label=1):", payload["metrics_pos1"])
    print(f"Wrote predictions -> {pred_out_path}")
    print(f"Wrote -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix

from experiments._load_modules import load_rules_module, repo_root


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate rule baseline on test.csv.")
    parser.add_argument(
        "--test",
        dest="test_csv",
        default=str(Path("data") / "splits" / "test.csv"),
        help="Path to test.csv (default: data/splits/test.csv)",
    )
    parser.add_argument(
        "--out",
        dest="out_json",
        default=str(Path("reports") / "metrics_rules_test.json"),
        help="Where to write metrics JSON (default: reports/metrics_rules_test.json)",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=6,
        help="Rule score threshold (default 6; matches RuleConfig.threshold default)",
    )
    parser.add_argument(
        "--pred_out",
        dest="pred_out_csv",
        default=str(Path("reports") / "pred_rules_test.csv"),
        help="Where to write per-row predictions (default: reports/pred_rules_test.csv)",
    )
    args = parser.parse_args(argv)

    test_df = pd.read_csv(Path(args.test_csv))
    if not {"label", "message"}.issubset(test_df.columns):
        raise ValueError("Expected CSV columns: label, message")

    y_true = test_df["label"].astype(int).tolist()
    messages = test_df["message"].astype(str).tolist()

    rules = load_rules_module()
    cfg = rules.RuleConfig(threshold=args.threshold)

    y_pred = []
    for msg in messages:
        res = rules.detect_smishing(msg, config=cfg)
        y_pred.append(1 if bool(res["is_suspicious"]) else 0)

    report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist()

    out_path = repo_root() / Path(args.out_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    pred_out_path = repo_root() / Path(args.pred_out_csv)
    pred_out_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"y_true": y_true, "y_pred": list(map(int, y_pred))}).to_csv(pred_out_path, index=False)

    payload = {
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "test_csv": str(Path(args.test_csv)),
        "n_test": len(messages),
        "rule_threshold": args.threshold,
        "predictions_csv": str(pred_out_path),
        "confusion_matrix_labels_[0,1]": cm,
        "metrics_pos1": {
            "accuracy": report.get("accuracy"),
            "precision": report.get("1", {}).get("precision"),
            "recall": report.get("1", {}).get("recall"),
            "f1": report.get("1", {}).get("f1-score"),
        },
        "classification_report": report,
    }

    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("Rules test metrics (pos_label=1):", payload["metrics_pos1"])
    print(f"Wrote predictions -> {pred_out_path}")
    print(f"Wrote -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

