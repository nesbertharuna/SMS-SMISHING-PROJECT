from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import joblib
import pandas as pd
from sklearn.metrics import classification_report

try:
    from experiments._load_modules import load_tfidf_features_module, repo_root
except ModuleNotFoundError:
    from _load_modules import load_tfidf_features_module, repo_root


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Train TF-IDF + LogisticRegression smishing detector.")
    parser.add_argument(
        "--train",
        dest="train_csv",
        default=str(Path("data") / "splits" / "train.csv"),
        help="Path to train.csv (default: data/splits/train.csv)",
    )
    parser.add_argument(
        "--val",
        dest="val_csv",
        default=str(Path("data") / "splits" / "val.csv"),
        help="Path to val.csv (default: data/splits/val.csv)",
    )
    parser.add_argument(
        "--artifact",
        default=str(Path("ml-backend") / "artifacts" / "pipeline_lr_tfidf.joblib"),
        help="Where to save the fitted pipeline (default: ml-backend/artifacts/pipeline_lr_tfidf.joblib)",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default 42)")
    args = parser.parse_args(argv)

    train_df = pd.read_csv(Path(args.train_csv))
    val_df = pd.read_csv(Path(args.val_csv))

    if not {"label", "message"}.issubset(train_df.columns) or not {"label", "message"}.issubset(val_df.columns):
        raise ValueError("Expected CSV columns: label, message")

    x_train = train_df["message"].astype(str).tolist()
    y_train = train_df["label"].astype(int).tolist()
    x_val = val_df["message"].astype(str).tolist()
    y_val = val_df["label"].astype(int).tolist()

    tfidf_features = load_tfidf_features_module()
    pipe = tfidf_features.build_tfidf_pipeline()
    pipe.fit(x_train, y_train)

    # Validation-only numbers (test must be evaluated in a separate script).
    y_val_pred = pipe.predict(x_val)
    report = classification_report(y_val, y_val_pred, output_dict=True, zero_division=0)

    artifact_path = repo_root() / Path(args.artifact)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, artifact_path)

    meta = {
        "artifact": str(artifact_path),
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
        "seed": args.seed,
        "model": "tfidf+logreg(class_weight=balanced)",
        "data": {
            "train_csv": str(Path(args.train_csv)),
            "val_csv": str(Path(args.val_csv)),
            "n_train": len(x_train),
            "n_val": len(x_val),
        },
        "val_metrics": {
            "accuracy": report.get("accuracy"),
            "precision_pos1": report.get("1", {}).get("precision"),
            "recall_pos1": report.get("1", {}).get("recall"),
            "f1_pos1": report.get("1", {}).get("f1-score"),
        },
    }

    meta_path = artifact_path.with_suffix(".meta.json")
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"Saved model -> {artifact_path}")
    print(f"Saved metadata -> {meta_path}")
    print("Validation metrics (pos_label=1):", meta["val_metrics"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
