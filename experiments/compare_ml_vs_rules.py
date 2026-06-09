from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd
from scipy.stats import binomtest
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

try:
    from experiments._load_modules import repo_root
except ModuleNotFoundError:
    from _load_modules import repo_root


def _metrics(y_true, y_pred) -> dict:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_pos1": float(precision_score(y_true, y_pred, pos_label=1, zero_division=0)),
        "recall_pos1": float(recall_score(y_true, y_pred, pos_label=1, zero_division=0)),
        "f1_pos1": float(f1_score(y_true, y_pred, pos_label=1, zero_division=0)),
    }


def mcnemar_exact(y_true, y_a, y_b) -> dict:
    """
    Exact McNemar test using a binomial test on discordant pairs:
      b = A correct, B wrong
      c = A wrong, B correct
    Under H0: b and c equally likely (p=0.5).
    """
    b = 0
    c = 0
    for yt, ya, yb in zip(y_true, y_a, y_b):
        a_correct = int(ya == yt)
        b_correct = int(yb == yt)
        if a_correct == 1 and b_correct == 0:
            b += 1
        elif a_correct == 0 and b_correct == 1:
            c += 1

    n = b + c
    p_value = float(binomtest(min(b, c), n=n, p=0.5, alternative="two-sided").pvalue) if n > 0 else 1.0
    return {"b_ml_correct_rules_wrong": b, "c_ml_wrong_rules_correct": c, "n_discordant": n, "p_value": p_value}


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Compare ML vs rules on the same test set (metrics + McNemar).")
    parser.add_argument(
        "--test",
        dest="test_csv",
        default=str(Path("data") / "splits" / "test.csv"),
        help="Path to test.csv (default: data/splits/test.csv)",
    )
    parser.add_argument(
        "--pred_ml",
        default=str(Path("reports") / "pred_ml_test.csv"),
        help="CSV with y_pred for ML (default: reports/pred_ml_test.csv)",
    )
    parser.add_argument(
        "--pred_rules",
        default=str(Path("reports") / "pred_rules_test.csv"),
        help="CSV with y_pred for rules (default: reports/pred_rules_test.csv)",
    )
    parser.add_argument(
        "--out",
        dest="out_json",
        default=str(Path("reports") / "compare_ml_vs_rules.json"),
        help="Where to write comparison JSON (default: reports/compare_ml_vs_rules.json)",
    )
    args = parser.parse_args(argv)

    test_df = pd.read_csv(Path(args.test_csv))
    y_true = test_df["label"].astype(int).tolist()

    pred_ml_df = pd.read_csv(repo_root() / Path(args.pred_ml))
    pred_rules_df = pd.read_csv(repo_root() / Path(args.pred_rules))

    y_ml = pred_ml_df["y_pred"].astype(int).tolist()
    y_rules = pred_rules_df["y_pred"].astype(int).tolist()

    if not (len(y_true) == len(y_ml) == len(y_rules)):
        raise ValueError("Length mismatch between test labels and prediction files.")

    metrics_ml = _metrics(y_true, y_ml)
    metrics_rules = _metrics(y_true, y_rules)
    mcnemar = mcnemar_exact(y_true, y_ml, y_rules)

    out = {
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "test_csv": str(Path(args.test_csv)),
        "pred_ml": str(Path(args.pred_ml)),
        "pred_rules": str(Path(args.pred_rules)),
        "metrics": {"ml": metrics_ml, "rules": metrics_rules},
        "mcnemar_exact": mcnemar,
    }

    out_path = repo_root() / Path(args.out_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print("ML:", metrics_ml)
    print("Rules:", metrics_rules)
    print("McNemar:", mcnemar)
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
from scipy.stats import binomtest
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

from experiments._load_modules import repo_root


def _metrics(y_true, y_pred) -> dict:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_pos1": float(precision_score(y_true, y_pred, pos_label=1, zero_division=0)),
        "recall_pos1": float(recall_score(y_true, y_pred, pos_label=1, zero_division=0)),
        "f1_pos1": float(f1_score(y_true, y_pred, pos_label=1, zero_division=0)),
    }


def mcnemar_exact(y_true, y_a, y_b) -> dict:
    """
    Exact McNemar test using a binomial test on discordant pairs:
      b = A correct, B wrong
      c = A wrong, B correct
    Under H0: b and c equally likely (p=0.5).
    """
    b = 0
    c = 0
    for yt, ya, yb in zip(y_true, y_a, y_b):
        a_correct = int(ya == yt)
        b_correct = int(yb == yt)
        if a_correct == 1 and b_correct == 0:
            b += 1
        elif a_correct == 0 and b_correct == 1:
            c += 1

    n = b + c
    p_value = float(binomtest(min(b, c), n=n, p=0.5, alternative="two-sided").pvalue) if n > 0 else 1.0
    return {"b_ml_correct_rules_wrong": b, "c_ml_wrong_rules_correct": c, "n_discordant": n, "p_value": p_value}


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Compare ML vs rules on the same test set (metrics + McNemar).")
    parser.add_argument(
        "--test",
        dest="test_csv",
        default=str(Path("data") / "splits" / "test.csv"),
        help="Path to test.csv (default: data/splits/test.csv)",
    )
    parser.add_argument(
        "--pred_ml",
        default=str(Path("reports") / "pred_ml_test.csv"),
        help="CSV with y_pred for ML (default: reports/pred_ml_test.csv)",
    )
    parser.add_argument(
        "--pred_rules",
        default=str(Path("reports") / "pred_rules_test.csv"),
        help="CSV with y_pred for rules (default: reports/pred_rules_test.csv)",
    )
    parser.add_argument(
        "--out",
        dest="out_json",
        default=str(Path("reports") / "compare_ml_vs_rules.json"),
        help="Where to write comparison JSON (default: reports/compare_ml_vs_rules.json)",
    )
    args = parser.parse_args(argv)

    test_df = pd.read_csv(Path(args.test_csv))
    y_true = test_df["label"].astype(int).tolist()

    pred_ml_df = pd.read_csv(repo_root() / Path(args.pred_ml))
    pred_rules_df = pd.read_csv(repo_root() / Path(args.pred_rules))

    y_ml = pred_ml_df["y_pred"].astype(int).tolist()
    y_rules = pred_rules_df["y_pred"].astype(int).tolist()

    if not (len(y_true) == len(y_ml) == len(y_rules)):
        raise ValueError("Length mismatch between test labels and prediction files.")

    metrics_ml = _metrics(y_true, y_ml)
    metrics_rules = _metrics(y_true, y_rules)
    mcnemar = mcnemar_exact(y_true, y_ml, y_rules)

    out = {
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
        "test_csv": str(Path(args.test_csv)),
        "pred_ml": str(Path(args.pred_ml)),
        "pred_rules": str(Path(args.pred_rules)),
        "metrics": {"ml": metrics_ml, "rules": metrics_rules},
        "mcnemar_exact": mcnemar,
    }

    out_path = repo_root() / Path(args.out_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print("ML:", metrics_ml)
    print("Rules:", metrics_rules)
    print("McNemar:", mcnemar)
    print(f"Wrote -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

