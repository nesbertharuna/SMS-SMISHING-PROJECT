from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Tuple

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline


def _load_preprocess_sms_to_string():
    """
    Load `preprocess_sms_to_string` from `ml-backend/preprocessing/clean_text.py`
    without requiring package (__init__.py) setup.
    """
    backend_root = Path(__file__).resolve().parents[1]  # .../ml-backend
    clean_text_path = backend_root / "preprocessing" / "clean_text.py"

    spec = importlib.util.spec_from_file_location("clean_text", clean_text_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {clean_text_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.preprocess_sms_to_string


preprocess_sms_to_string = _load_preprocess_sms_to_string()


@dataclass(frozen=True)
class NbTfidfConfig:
    max_features: Optional[int] = 30000
    ngram_range: Tuple[int, int] = (1, 2)
    min_df: int = 2
    max_df: float = 0.95
    sublinear_tf: bool = True
    alpha: float = 1.0  # MultinomialNB smoothing


def build_nb_pipeline(
    *,
    cfg: Optional[NbTfidfConfig] = None,
    stopwords: Optional[Sequence[str]] = None,
    keep_numbers: bool = True,
) -> Pipeline:
    """
    raw_text -> preprocessing -> TF-IDF -> MultinomialNB
    """
    c = cfg or NbTfidfConfig()

    def _preprocess(doc: str) -> str:
        return preprocess_sms_to_string(doc, stopwords=stopwords, keep_numbers=keep_numbers)

    vectorizer = TfidfVectorizer(
        preprocessor=_preprocess,
        tokenizer=str.split,
        token_pattern=None,
        lowercase=False,
        max_features=c.max_features,
        ngram_range=c.ngram_range,
        min_df=c.min_df,
        max_df=c.max_df,
        sublinear_tf=c.sublinear_tf,
    )
    nb = MultinomialNB(alpha=c.alpha)

    return Pipeline(
        steps=[
            ("tfidf", vectorizer),
            ("nb", nb),
        ]
    )


def train_nb_spam_detector(
    texts: Sequence[str],
    labels: Sequence[int] | Sequence[str],
    *,
    cfg: Optional[NbTfidfConfig] = None,
    stopwords: Optional[Sequence[str]] = None,
    keep_numbers: bool = True,
    test_size: float = 0.2,
    random_state: int = 42,
    model_out_path: Optional[str | Path] = None,
) -> Tuple[Pipeline, Dict[str, Any]]:
    """
    Train/evaluate a Naive Bayes spam detector.

    - `labels` can be "ham"/"spam" or 0/1 (or any 2+ class labels).
    - If `model_out_path` is set, saves the fitted pipeline via joblib.
    """
    x_train, x_test, y_train, y_test = train_test_split(
        list(texts),
        list(labels),
        test_size=test_size,
        random_state=random_state,
        stratify=list(labels),
    )

    model = build_nb_pipeline(cfg=cfg, stopwords=stopwords, keep_numbers=keep_numbers)
    model.fit(x_train, y_train)

    y_pred = model.predict(x_test)
    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    metrics: Dict[str, Any] = {
        "test_size": test_size,
        "n_train": len(x_train),
        "n_test": len(x_test),
        "classification_report": report,
    }

    if model_out_path is not None:
        model_out_path = Path(model_out_path)
        model_out_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, model_out_path)
        metrics["model_path"] = str(model_out_path)

    return model, metrics


def load_model(path: str | Path) -> Pipeline:
    return joblib.load(Path(path))


if __name__ == "__main__":
    # Minimal example (replace with your dataset loader).
    sample_texts = [
        "WINNER!! Claim your prize now by calling 09061701461",
        "Are we still on for dinner tonight?",
        "URGENT! Your account has been compromised, verify now",
        "Ok thanks",
    ]
    sample_labels = ["spam", "ham", "spam", "ham"]

    model, m = train_nb_spam_detector(sample_texts, sample_labels, model_out_path=Path("artifacts") / "nb_tfidf.joblib")
    print("Weighted F1:", m["classification_report"]["weighted avg"]["f1-score"])
