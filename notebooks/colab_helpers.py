"""Helpers for running the full smishing system inside Google Colab."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def setup_repo(repo: Path) -> None:
    """Add repo paths so all modules import correctly."""
    repo = repo.resolve()
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))
    rule_engine = repo / "ml-backend" / "rule-engine"
    if str(rule_engine) not in sys.path:
        sys.path.insert(0, str(rule_engine))


def verify_system_files(repo: Path) -> List[str]:
    """Return list of missing paths (empty = all present)."""
    required = [
        "ml-backend/preprocessing/clean_text.py",
        "ml-backend/feature-extraction/tfidf_features.py",
        "ml-backend/models/explain_lr_tfidf.py",
        "ml-backend/rule-engine/rules.py",
        "ml-backend/rule-engine/rule_based_baseline.py",
        "ml-backend/api/classify.py",
        "ml-backend/dataset/Dataset1.csv",
        "ml-backend/requirements.txt",
        "experiments/train.py",
        "experiments/evaluate_ml.py",
        "experiments/evaluate_rules.py",
        "experiments/compare_ml_vs_rules.py",
        "scripts/train_full_pipeline.py",
        "scripts/load_dataset1.py",
        "scripts/make_splits.py",
        "scripts/collect_sms.py",
        "scripts/download_datasets.py",
        "scripts/merge_datasets.py",
        "scripts/colab_bootstrap.py",
        "webapp/smishui/app/page.tsx",
        "mobile-app/react-native-app/app/(tabs)/index.tsx",
    ]
    missing = [p for p in required if not (repo / p).exists()]
    return missing


def run_script(repo: Path, rel_script: str, *args: str) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(repo / rel_script), *args]
    print(">", " ".join(cmd))
    return subprocess.run(cmd, cwd=repo, capture_output=True, text=True)


def load_ml_classifier(repo: Path, artifact: str = "ml-backend/artifacts/pipeline_lr_tfidf.joblib"):
    setup_repo(repo)
    classify_path = repo / "ml-backend" / "api" / "classify.py"
    spec = importlib.util.spec_from_file_location("smish_classify", classify_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {classify_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    pipeline = mod._load_pipeline(artifact)

    def classify(text: str, top_k: int = 5) -> Dict[str, Any]:
        text = str(text).strip()
        if not text:
            raise ValueError("SMS text is required.")
        return mod._predict_and_explain(pipeline=pipeline, text=text, top_k=top_k)

    return classify


def load_rule_classifier(repo: Path):
    setup_repo(repo)
    from rule_based_baseline import classify as rule_classify  # noqa: PLC0415

    return rule_classify


def format_ml_result(result: Dict[str, Any]) -> str:
    lines = [
        f"**Label:** {result['label'].upper()}",
        f"**Smishing score:** {result.get('risk_percent_smishing', 'n/a')}%",
        "",
        result.get("verdict_plain", ""),
    ]
    for line in result.get("signals_toward_smishing", []):
        lines.append(f"- {line}")
    for line in result.get("signals_toward_benign", []):
        lines.append(f"- {line}")
    return "\n".join(lines)


def format_rule_result(result: Dict[str, Any]) -> str:
    return (
        f"**Label:** {result['label'].upper()}\n"
        f"**Score:** {result['score']}\n\n"
        f"{result.get('verdict_plain', '')}\n"
        f"**Reasons:** {', '.join(result.get('reasons', [])) or 'none'}"
    )


def analyze_both(repo: Path, text: str) -> Dict[str, str]:
    ml_fn = load_ml_classifier(repo)
    rule_fn = load_rule_classifier(repo)
    return {
        "ml": format_ml_result(ml_fn(text)),
        "rules": format_rule_result(rule_fn(text)),
    }


def read_json_report(repo: Path, rel_path: str) -> Optional[Dict[str, Any]]:
    path = repo / rel_path
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
