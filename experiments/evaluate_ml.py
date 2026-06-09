from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import joblib
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix

try:
    from experiments._load_modules import load_tfidf_features_module, repo_root
except ModuleNotFoundError:
    from _load_modules import load_tfidf_features_module, repo_root


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate saved ML pipeline on test.csv.")
    parser.add_argument(
        "--test",
        dest="test_csv",
        default=str(Path("data") / "splits" / "test.csv"),
        help="Path to test.csv (default: data/splits/test.csv)",
    )
    parser.add_argument(
        "--artifact",
        default=str(Path("ml-backend") / "artifacts" / "pipeline_lr_tfidf.joblib"),
        help="Path to saved joblib pipeline (default: ml-backend/artifacts/pipeline_lr_tfidf.joblib)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help=(
            "Write to fixed filenames reports/metrics_ml_test.json and reports/pred_ml_test.csv "
            "(replaces prior runs). Default is timestamped filenames so runs do not overwrite."
        ),
    )
    parser.add_argument(
        "--out",
        dest="out_json",
        default=None,
        help=(
            "Metrics JSON path (optional). If omitted with --overwrite, uses "
            "reports/metrics_ml_test.json; otherwise uses a timestamped name under reports/."
        ),
    )
    parser.add_argument(
        "--pred_out",
        dest="pred_out_csv",
        default=None,
        help=(
            "Predictions CSV path (optional). If omitted with --overwrite, uses "
            "reports/pred_ml_test.csv; otherwise pairs with metrics file timestamp."
        ),
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Optional probability threshold for class=1 (requires predict_proba). If omitted, uses model.predict().",
    )
    args = parser.parse_args(argv)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    reports = Path("reports")
    if args.overwrite:
        out_rel = args.out_json or str(reports / "metrics_ml_test.json")
        pred_rel = args.pred_out_csv or str(reports / "pred_ml_test.csv")
    else:
        out_rel = args.out_json or str(reports / f"metrics_ml_test_{stamp}.json")
        pred_rel = args.pred_out_csv or str(reports / f"pred_ml_test_{stamp}.csv")

    test_df = pd.read_csv(Path(args.test_csv))
    if not {"label", "message"}.issubset(test_df.columns):
        raise ValueError("Expected CSV columns: label, message")

    x_test = test_df["message"].astype(str).tolist()
    y_true = test_df["label"].astype(int).tolist()

    # Ensure the dynamic module name used during pickling is importable at load time.
    load_tfidf_features_module()
    artifact_path = repo_root() / Path(args.artifact)
    pipe = joblib.load(artifact_path)

    y_proba_1 = None
    if args.threshold is not None:
        if not hasattr(pipe, "predict_proba"):
            raise ValueError("--threshold was provided but the pipeline does not support predict_proba().")
        proba = pipe.predict_proba(x_test)
        # Binary classifier -> take probability of class=1
        y_proba_1 = proba[:, 1]
        y_pred = (y_proba_1 >= float(args.threshold)).astype(int)
    else:
        y_pred = pipe.predict(x_test)

    report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist()  # [[tn, fp],[fn,tp]]
    tn, fp = cm[0]
    fn, tp = cm[1]

    out_path = repo_root() / Path(out_rel)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    pred_out_path = repo_root() / Path(pred_rel)
    pred_out_path.parent.mkdir(parents=True, exist_ok=True)
    pred_df = pd.DataFrame({"y_true": y_true, "y_pred": list(map(int, y_pred))})
    if y_proba_1 is not None:
        pred_df["p1"] = y_proba_1
    pred_df.to_csv(pred_out_path, index=False)

    payload = {
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "artifact": str(artifact_path),
        "test_csv": str(Path(args.test_csv)),
        "n_test": len(x_test),
        "predictions_csv": str(pred_out_path),
        "threshold": args.threshold,
        "confusion_matrix_labels_[0,1]": cm,
        "confusion_matrix_named": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
        "metrics_pos1": {
            "accuracy": report.get("accuracy"),
            "precision": report.get("1", {}).get("precision"),
            "recall": report.get("1", {}).get("recall"),
            "f1": report.get("1", {}).get("f1-score"),
        },
        "classification_report": report,
    }

    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(flush=True)
    print("ML test metrics (pos_label=1):", payload["metrics_pos1"])
    print("Confusion matrix (tn, fp, fn, tp):", payload["confusion_matrix_named"])
    print(f"Wrote predictions -> {pred_out_path}")
    print(f"Wrote -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
