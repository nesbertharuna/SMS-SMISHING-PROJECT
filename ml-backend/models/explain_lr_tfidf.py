from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Sequence

import numpy as np


@dataclass(frozen=True)
class TokenContribution:
    token: str
    contribution: float


def explain_tfidf_logreg(
    *,
    pipeline: Any,
    text: str,
    top_k: int = 10,
) -> Dict[str, object]:
    """
    Explain a TF-IDF + LogisticRegression sklearn Pipeline decision for a single text.

    Assumptions:
    - pipeline has steps named: 'tfidf' (TfidfVectorizer) and 'clf' (LogisticRegression-like)
    - binary classification with class=1 representing 'smishing'

    Returns:
      {
        "p_smishing": float | None,
        "logit": float,
        "top_positive": [{token, contribution}, ...],
        "top_negative": [{token, contribution}, ...],
      }
    """
    if not hasattr(pipeline, "named_steps"):
        raise ValueError("Expected a sklearn Pipeline with named_steps.")
    if "tfidf" not in pipeline.named_steps or "clf" not in pipeline.named_steps:
        raise ValueError("Expected pipeline steps named 'tfidf' and 'clf'.")

    vec = pipeline.named_steps["tfidf"]
    clf = pipeline.named_steps["clf"]

    if not hasattr(vec, "get_feature_names_out"):
        raise ValueError("Vectorizer does not support get_feature_names_out().")
    if not hasattr(clf, "coef_") or not hasattr(clf, "intercept_"):
        raise ValueError("Classifier does not look like LogisticRegression (missing coef_/intercept_).")

    X = vec.transform([text])  # (1, n_features) sparse
    feature_names = vec.get_feature_names_out()

    # For binary LR in sklearn, coef_ shape is (1, n_features), intercept_ shape (1,)
    w = np.asarray(clf.coef_)[0]
    b = float(np.asarray(clf.intercept_)[0])

    # Contribution per feature = x_i * w_i
    x = X.tocsr()
    idxs = x.indices
    vals = x.data
    contribs = vals * w[idxs]

    # logit = intercept + sum(contribs)
    logit = b + float(contribs.sum())

    # Pick top positive and negative contributions among present features.
    if contribs.size == 0:
        top_pos: List[TokenContribution] = []
        top_neg: List[TokenContribution] = []
    else:
        order = np.argsort(contribs)
        neg_idxs = order[:top_k]
        pos_idxs = order[::-1][:top_k]

        top_neg = [
            TokenContribution(token=str(feature_names[int(idxs[i])]), contribution=float(contribs[i]))
            for i in neg_idxs
            if contribs[i] < 0
        ]
        top_pos = [
            TokenContribution(token=str(feature_names[int(idxs[i])]), contribution=float(contribs[i]))
            for i in pos_idxs
            if contribs[i] > 0
        ]

    p_smishing = None
    if hasattr(pipeline, "predict_proba"):
        try:
            proba = pipeline.predict_proba([text])
            p_smishing = float(proba[0][1])
        except Exception:
            p_smishing = None

    return {
        "p_smishing": p_smishing,
        "logit": logit,
        "top_positive": [tc.__dict__ for tc in top_pos],
        "top_negative": [tc.__dict__ for tc in top_neg],
    }

