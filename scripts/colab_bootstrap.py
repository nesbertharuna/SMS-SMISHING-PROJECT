from __future__ import annotations

import argparse
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _run(argv: list[str], *, cwd: Path) -> None:
    print(">", " ".join(argv), flush=True)
    subprocess.run(argv, cwd=cwd, check=True)


def install_deps(repo: Path, *, with_ui: bool = False) -> None:
    req = repo / "ml-backend" / "requirements.txt"
    if not req.exists():
        raise FileNotFoundError(f"Missing requirements file: {req}")
    _run([sys.executable, "-m", "pip", "install", "-q", "-r", str(req)], cwd=repo)
    if with_ui:
        _run([sys.executable, "-m", "pip", "install", "-q", "gradio>=4.0,<6.0"], cwd=repo)


def download_uci(repo: Path) -> Path:
    raw_dir = repo / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    out_path = raw_dir / "SMSSpamCollection"
    if out_path.exists() and out_path.stat().st_size > 0:
        print(f"UCI file already present: {out_path}")
        return out_path

    zip_path = raw_dir / "smsspamcollection.zip"
    url = "https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip"
    print(f"Downloading UCI SMS Spam Collection from {url}")
    urllib.request.urlretrieve(url, zip_path)

    with zipfile.ZipFile(zip_path, "r") as zf:
        member = next((n for n in zf.namelist() if n.endswith("SMSSpamCollection")), None)
        if member is None:
            raise RuntimeError("SMSSpamCollection not found inside UCI zip.")
        out_path.write_bytes(zf.read(member))

    print(f"Wrote {out_path} ({out_path.stat().st_size} bytes)")
    return out_path


def verify_dataset1(repo: Path) -> dict:
    import pandas as pd

    path = repo / "ml-backend" / "dataset" / "Dataset1.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing dataset: {path}")

    df = pd.read_csv(path)
    unique_messages = int(df["message"].nunique())
    stats = {
        "path": str(path),
        "rows": len(df),
        "unique_messages": unique_messages,
        "benign": int((df["label"].astype(str).str.lower() == "benign").sum()),
        "smishing": int((df["label"].astype(str).str.lower() == "smishing").sum()),
    }

    print("Dataset1.csv")
    print(f"  rows:            {stats['rows']}")
    print(f"  unique messages: {stats['unique_messages']}")
    print(f"  benign:          {stats['benign']}")
    print(f"  smishing:        {stats['smishing']}")

    if unique_messages < 50:
        print(
            "\nWARNING: Very few unique messages. Model metrics will be unstable. "
            "Use DATASET='uci' in the Colab notebook for a larger benchmark dataset."
        )
    return stats


def verify_env() -> None:
    import importlib

    print(f"Python: {sys.version.split()[0]} @ {sys.executable}")
    for pkg in ("numpy", "pandas", "sklearn", "joblib", "scipy"):
        mod = importlib.import_module(pkg if pkg != "sklearn" else "sklearn")
        version = getattr(mod, "__version__", "unknown")
        print(f"  {pkg}: {version}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Colab bootstrap helpers for the smishing project.")
    parser.add_argument("--install-deps", action="store_true", help="pip install ml-backend/requirements.txt")
    parser.add_argument("--with-ui", action="store_true", help="Also install gradio (use with --install-deps)")
    parser.add_argument("--download-uci", action="store_true", help="Download UCI SMSSpamCollection into data/raw/")
    parser.add_argument("--verify-dataset", action="store_true", help="Print Dataset1.csv stats and warnings")
    parser.add_argument("--verify-env", action="store_true", help="Print Python and package versions")
    args = parser.parse_args(argv)

    repo = repo_root()
    if not any((args.install_deps, args.download_uci, args.verify_dataset, args.verify_env)):
        parser.error("Pick at least one action flag.")

    if args.install_deps:
        install_deps(repo, with_ui=args.with_ui)
    if args.download_uci:
        download_uci(repo)
    if args.verify_dataset:
        verify_dataset1(repo)
    if args.verify_env:
        verify_env()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
