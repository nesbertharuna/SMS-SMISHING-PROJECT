from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def repo_root() -> Path:
    # .../SMS SMISHING SOFTWARE/experiments/_load_modules.py -> repo root is parents[1]
    return Path(__file__).resolve().parents[1]


def _load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module '{name}' from {path}")
    mod = importlib.util.module_from_spec(spec)
    # Required for decorators/introspection relying on sys.modules during import time.
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def load_tfidf_features_module() -> ModuleType:
    p = repo_root() / "ml-backend" / "feature-extraction" / "tfidf_features.py"
    return _load_module("tfidf_features", p)


def load_rules_module() -> ModuleType:
    p = repo_root() / "ml-backend" / "rule-engine" / "rules.py"
    return _load_module("rules", p)
