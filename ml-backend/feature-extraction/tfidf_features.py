from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

import importlib.util
from pathlib import Path


def _load_preprocess_sms_to_string():
    """
    Load `preprocess_sms_to_string` from `ml-backend/prepocessing/clean_text.py`
    without requiring package (__init__.py) setup.
    """
    backend_root = Path(__file__).resolve().parents[1]  # .../ml-backend
    clean_text_path = backend_root / "prepocessing" / "clean_text.py"

    spec = importlib.util.spec_from_file_location("clean_text", clean_text_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {clean_text_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.preprocess_sms_to_string


preprocess_sms_to_string = _load_preprocess_sms_to_string()


@dataclass(frozen=True)
class TfidfConfig:
    max_features: Optional[int] = 20000
    ngram_range: Tuple[int, int] = (1, 2)
    min_df: int = 2
    max_df: float = 0.95
    sublinear_tf: bool = True


def build_tfidf_pipeline(
    *,
    tfidf: Optional[TfidfConfig] = None,
    stopwords: Optional[Sequence[str]] = None,
    keep_numbers: bool = True,
    clf: Optional[Any] = None,
) -> Pipeline:
    """
    Create a scikit-learn Pipeline:
      raw_text -> preprocessing -> TF-IDF -> classifier

    - Preprocessing uses `preprocess_sms_to_string` from `prepocessing/clean_text.py`.
    - Default classifier is LogisticRegression (strong baseline for text).
    """
    cfg = tfidf or TfidfConfig()
    classifier = clf or LogisticRegression(max_iter=2000, n_jobs=None, class_weight="balanced")

    def _preprocess(doc: str) -> str:
        return preprocess_sms_to_string(doc, stopwords=stopwords, keep_numbers=keep_numbers)

    vectorizer = TfidfVectorizer(
        preprocessor=_preprocess,
        tokenizer=str.split,  # tokens are space-separated from preprocess_sms_to_string
        token_pattern=None,  # required when providing a custom tokenizer
        lowercase=False,  # we already lowercase in preprocess
        max_features=cfg.max_features,
        ngram_range=cfg.ngram_range,
        min_df=cfg.min_df,
        max_df=cfg.max_df,
        sublinear_tf=cfg.sublinear_tf,
    )

    return Pipeline(
        steps=[
            ("tfidf", vectorizer),
            ("clf", classifier),
        ]
    )


def train_and_evaluate(
    texts: Sequence[str],
    labels: Sequence[int] | Sequence[str],
    *,
    test_size: float = 0.2,
    random_state: int = 42,
    tfidf: Optional[TfidfConfig] = None,
    stopwords: Optional[Sequence[str]] = None,
    keep_numbers: bool = True,
    clf: Optional[Any] = None,
) -> Tuple[Pipeline, Dict[str, Any]]:
    """
    Train a TF-IDF model and return (pipeline, metrics).

    `labels` can be strings (e.g., "ham"/"spam") or ints (0/1).
    """
    x_train, x_test, y_train, y_test = train_test_split(
        list(texts),
        list(labels),
        test_size=test_size,
        random_state=random_state,
        stratify=list(labels),
    )

    pipe = build_tfidf_pipeline(tfidf=tfidf, stopwords=stopwords, keep_numbers=keep_numbers, clf=clf)
    pipe.fit(x_train, y_train)

    y_pred = pipe.predict(x_test)
    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

    metrics: Dict[str, Any] = {
        "test_size": test_size,
        "n_train": len(x_train),
        "n_test": len(x_test),
        "classification_report": report,
    }
    return pipe, metrics


def featurize_texts(
    texts: Iterable[str],
    *,
    tfidf: Optional[TfidfConfig] = None,
    stopwords: Optional[Sequence[str]] = None,
    keep_numbers: bool = True,
) -> Tuple[TfidfVectorizer, Any]:
    """
    Convenience helper if you only want TF-IDF features (no classifier).
    Returns (vectorizer, X_sparse).
    """
    cfg = tfidf or TfidfConfig()

    def _preprocess(doc: str) -> str:
        return preprocess_sms_to_string(doc, stopwords=stopwords, keep_numbers=keep_numbers)

    vectorizer = TfidfVectorizer(
        preprocessor=_preprocess,
        tokenizer=str.split,
        token_pattern=None,
        lowercase=False,
        max_features=cfg.max_features,
        ngram_range=cfg.ngram_range,
        min_df=cfg.min_df,
        max_df=cfg.max_df,
        sublinear_tf=cfg.sublinear_tf,
    )
    x = vectorizer.fit_transform(list(texts))
    return vectorizer, x


if __name__ == "__main__":
    # Minimal example (replace with your real dataset loader).
    sample_texts: List[str] = [
        "Free entry in 2 a wkly comp to win FA Cup final tkts. Text FA to 87121",
        "Hey are we still meeting at 7?",
        "URGENT! You have won a 1 week FREE membership. Call now!",
        "Ok, see you soon.",
    ]
    sample_labels: List[str] = ["spam", "ham", "spam", "ham"]

    model, m = train_and_evaluate(sample_texts, sample_labels)
    print("Weighted F1:", m["classification_report"]["weighted avg"]["f1-score"])
