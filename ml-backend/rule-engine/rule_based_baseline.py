from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from rules import RuleConfig, detect_smishing


def classify(
    text: str,
    *,
    config: Optional[RuleConfig] = None,
    keywords: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """
    Classify a single SMS using the rule-based baseline.

    Returns a dict aligned with the ML classify API shape:
      - label: "smishing" | "benign"
      - y_pred: 1 | 0
      - score: rule engine risk score
      - reasons: triggered rule tags
      - matches: keyword/url/phone/phrase hits
    """
    kwargs: Dict[str, Any] = {"config": config or RuleConfig()}
    if keywords is not None:
        kwargs["keywords"] = keywords

    cfg = kwargs["config"]
    result = detect_smishing(text, **kwargs)
    is_smishing = bool(result["is_suspicious"])

    return {
        "label": "smishing" if is_smishing else "benign",
        "y_pred": 1 if is_smishing else 0,
        "score": int(result["score"]),
        "reasons": list(result["reasons"]),
        "matches": dict(result["matches"]),
        "verdict_plain": _verdict_plain(result, threshold=cfg.threshold),
    }


def predict_batch(
    messages: Sequence[str],
    *,
    config: Optional[RuleConfig] = None,
) -> List[int]:
    """Return binary predictions (1=smishing, 0=benign) for a list of messages."""
    cfg = config or RuleConfig()
    out: List[int] = []
    for msg in messages:
        res = detect_smishing(msg, config=cfg)
        out.append(1 if bool(res["is_suspicious"]) else 0)
    return out


def _verdict_plain(result: Dict[str, object], *, threshold: int) -> str:
    score = int(result["score"])
    label = "smishing" if bool(result["is_suspicious"]) else "benign"
    reasons = ", ".join(result["reasons"]) if result["reasons"] else "no strong cues"

    if label == "smishing":
        return (
            f"The rule engine classifies this as smishing (score {score}, threshold {threshold}). "
            f"Triggered signals: {reasons}."
        )
    return (
        f"The rule engine classifies this as benign (score {score}, below threshold {threshold}). "
        f"Observed signals: {reasons}."
    )


def evaluate_csv(
    test_csv: str | Path,
    *,
    threshold: int = 6,
    out_json: Optional[str | Path] = None,
    pred_out_csv: Optional[str | Path] = None,
) -> Dict[str, Any]:
    """
    Evaluate the rule baseline on a CSV with columns: label, message.
    Writes metrics JSON and predictions CSV when output paths are provided.
    """
    import pandas as pd
    from sklearn.metrics import classification_report, confusion_matrix

    test_path = Path(test_csv)
    df = pd.read_csv(test_path)
    if not {"label", "message"}.issubset(df.columns):
        raise ValueError("Expected CSV columns: label, message")

    cfg = RuleConfig(threshold=threshold)
    y_true = df["label"].astype(int).tolist()
    messages = df["message"].astype(str).tolist()
    y_pred = predict_batch(messages, config=cfg)

    report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist()
    tn, fp = cm[0]
    fn, tp = cm[1]

    payload: Dict[str, Any] = {
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "test_csv": str(test_path),
        "n_test": len(messages),
        "rule_threshold": threshold,
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

    if pred_out_csv is not None:
        pred_path = Path(pred_out_csv)
        pred_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"y_true": y_true, "y_pred": y_pred}).to_csv(pred_path, index=False)
        payload["predictions_csv"] = str(pred_path)

    if out_json is not None:
        out_path = Path(out_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        payload["metrics_json"] = str(out_path)

    return payload


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Rule-based smishing baseline: classify one message or evaluate a test CSV."
    )
    parser.add_argument("--text", default=None, help="Classify a single SMS string.")
    parser.add_argument(
        "--test",
        dest="test_csv",
        default=None,
        help="Evaluate on test CSV (columns: label, message).",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=6,
        help="Rule score threshold (default 6).",
    )
    parser.add_argument(
        "--out",
        dest="out_json",
        default=str(Path("reports") / "metrics_rules_test.json"),
        help="Metrics JSON path when using --test.",
    )
    parser.add_argument(
        "--pred_out",
        dest="pred_out_csv",
        default=str(Path("reports") / "pred_rules_test.csv"),
        help="Predictions CSV path when using --test.",
    )
    args = parser.parse_args(argv)

    if args.text:
        cfg = RuleConfig(threshold=args.threshold)
        out = classify(args.text, config=cfg)
        sys.stdout.write(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    if args.test_csv:
        repo_root = Path(__file__).resolve().parents[2]
        test_path = Path(args.test_csv)
        if not test_path.is_absolute():
            test_path = repo_root / test_path

        out_json = repo_root / Path(args.out_json)
        pred_csv = repo_root / Path(args.pred_out_csv)

        payload = evaluate_csv(
            test_path,
            threshold=args.threshold,
            out_json=out_json,
            pred_out_csv=pred_csv,
        )
        print("Rules test metrics (pos_label=1):", payload["metrics_pos1"])
        print("Confusion matrix (tn, fp, fn, tp):", payload["confusion_matrix_named"])
        print(f"Wrote predictions -> {pred_csv}")
        print(f"Wrote -> {out_json}")
        return 0

    parser.error("Provide --text for single-message classification or --test for CSV evaluation.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
