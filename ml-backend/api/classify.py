from __future__ import annotations

import json
import math
import sys
import importlib.util
from pathlib import Path
from typing import Any, Dict, List

import joblib


def _repo_root() -> Path:
    # .../ml-backend/api/classify.py -> repo root is parents[2]
    return Path(__file__).resolve().parents[2]


def _load_pipeline(artifact_rel: str) -> Any:
    artifact_path = _repo_root() / Path(artifact_rel)
    if not artifact_path.exists():
        raise FileNotFoundError(f"Missing model artifact: {artifact_path}")

    # Make sure the module name used when pickling the pipeline is importable.
    tfidf_path = _repo_root() / "ml-backend" / "feature-extraction" / "tfidf_features.py"
    spec = importlib.util.spec_from_file_location("tfidf_features", tfidf_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {tfidf_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["tfidf_features"] = mod
    spec.loader.exec_module(mod)

    return joblib.load(artifact_path)


def _influence_band(share_percent: float) -> str:
    if share_percent >= 28:
        return "high"
    if share_percent >= 14:
        return "moderate"
    return "light"


def _human_reason_bullets(
    raw_rows: List[Dict[str, Any]],
    *,
    toward: str,
) -> List[str]:
    """
    raw_rows: items with token + contribution (+ toward smishing = positive contrib, toward benign = negative).
    Produce short, plain-language bullets; shares are split among tokens shown (not global model internals).
    """
    if not raw_rows:
        return []

    strengths = [abs(float(r["contribution"])) for r in raw_rows]
    total = sum(strengths)
    if total <= 0:
        return []

    bullets: List[str] = []
    ordinal = ("Strongest cue", "Next cue", "Also notable")
    toward_text = (
        "smishing-like wording matching patterns seen in your training examples"
        if toward == "smishing"
        else "benign wording seen in ordinary training examples"
    )

    for i, r in enumerate(raw_rows):
        phrase = str(r.get("token", "")).strip() or "(unknown phrase)"
        share = (strengths[i] / total) * 100.0
        share_rounded = int(round(max(share, 1))) if total > 0 else 1
        band = _influence_band(share)
        band_words = {"high": "strong", "moderate": "moderate", "light": "light"}
        prefix = ordinal[i] if i < len(ordinal) else "Another phrase"

        bullets.append(
            f'{prefix}: “{phrase}” represents roughly {share_rounded}% of the surfaced cues leaning toward '
            f"{toward_text}. Influence looks {band_words.get(band, 'moderate')}."
        )
    return bullets


def _verdict_paragraph(
    *,
    label: str,
    p_smishing: float | None,
    reasons_smishing: List[str],
    reasons_benign: List[str],
) -> str:
    risk_pct = None
    if p_smishing is not None:
        try:
            pr = float(p_smishing)
            risk_pct = None if math.isnan(pr) else int(round(pr * 100))
        except (TypeError, ValueError):
            risk_pct = None

    if label == "smishing":
        if risk_pct is not None:
            head = (
                f"The model classifies this as smishing—its overall likelihood estimate for smishing-like "
                f"patterns is roughly {risk_pct}%."
            )
        else:
            head = "The model classifies this as smishing."
        if not reasons_smishing:
            head += (
                " It did not single out standout words; several tiny cues combined to cross its decision boundary."
            )
    else:
        if risk_pct is not None:
            head = (
                "The model classifies this as benign. Its estimated smishing-like score is about "
                f"{risk_pct}%, lower than typical smishing passages it learned from."
            )
        else:
            head = "The model classifies this as benign."
        if not reasons_benign and not reasons_smishing:
            head += (
                " There were no strong word-level contrasts to highlight—overall tone matched benign examples."
            )

    return head


def _predict_and_explain(*, pipeline: Any, text: str, top_k: int) -> Dict[str, object]:
    # Local import so this script stays usable even if other modules change.
    explain_mod_path = _repo_root() / "ml-backend" / "models" / "explain_lr_tfidf.py"
    if not explain_mod_path.exists():
        raise FileNotFoundError(f"Missing explain module: {explain_mod_path}")

    spec = importlib.util.spec_from_file_location("explain_lr_tfidf", explain_mod_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {explain_mod_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["explain_lr_tfidf"] = mod
    spec.loader.exec_module(mod)

    y_pred = int(pipeline.predict([text])[0])
    explanation = mod.explain_tfidf_logreg(pipeline=pipeline, text=text, top_k=int(top_k))

    label = "smishing" if y_pred == 1 else "benign"
    p_raw = explanation.get("p_smishing")
    raw_pos = explanation.get("top_positive", []) or []
    raw_neg = explanation.get("top_negative", []) or []

    reasons_smishing = _human_reason_bullets(raw_pos, toward="smishing")
    reasons_benign = _human_reason_bullets(raw_neg, toward="benign")
    verdict = _verdict_paragraph(
        label=label,
        p_smishing=float(p_raw) if p_raw is not None else None,
        reasons_smishing=reasons_smishing,
        reasons_benign=reasons_benign,
    )

    pct_out = None
    if p_raw is not None:
        try:
            pr = float(p_raw)
            pct_out = None if math.isnan(pr) else int(round(pr * 100))
        except (TypeError, ValueError):
            pct_out = None

    return {
        "label": label,
        "y_pred": y_pred,
        "risk_percent_smishing": pct_out,
        "verdict_plain": verdict,
        "signals_toward_smishing": reasons_smishing,
        "signals_toward_benign": reasons_benign,
        "explanation_note": (
            "Percentages describe how strongly each surfaced phrase leaned the model toward smishing versus "
            "benign cues, relative to other phrases listed—not a calibrated real-world probability for each phrase."
        ),
    }


def main() -> int:
    """
    Read JSON from stdin:
      { "text": "...", "top_k": 10, "artifact": "ml-backend/artifacts/pipeline_lr_tfidf.joblib" }
    Write JSON to stdout.
    """
    raw = sys.stdin.read()
    if not raw.strip():
        raise ValueError("Expected JSON on stdin.")

    req = json.loads(raw)
    text = str(req.get("text", "")).strip()
    if not text:
        raise ValueError("Field 'text' is required.")

    top_k = int(req.get("top_k", 10))
    artifact = str(req.get("artifact", "ml-backend/artifacts/pipeline_lr_tfidf.joblib"))

    pipe = _load_pipeline(artifact)
    out = _predict_and_explain(pipeline=pipe, text=text, top_k=top_k)
    sys.stdout.write(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

