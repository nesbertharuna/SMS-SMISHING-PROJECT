from __future__ import annotations

import urllib.request
import zipfile
from pathlib import Path
from typing import Optional

import pandas as pd


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


UCI_ZIP_URL = "https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip"


def download_uci_sms(*, dest_dir: Optional[Path] = None, force: bool = False) -> Path:
    """
    Download the UCI SMS Spam Collection into data/raw/SMSSpamCollection.
    Returns path to the raw tab-separated file.
    """
    raw_dir = dest_dir or (repo_root() / "data" / "raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    out_path = raw_dir / "SMSSpamCollection"

    if out_path.exists() and out_path.stat().st_size > 0 and not force:
        print(f"Already present: {out_path}")
        return out_path

    zip_path = raw_dir / "smsspamcollection.zip"
    print(f"Downloading UCI SMS Spam Collection...")
    urllib.request.urlretrieve(UCI_ZIP_URL, zip_path)

    with zipfile.ZipFile(zip_path, "r") as zf:
        member = next((n for n in zf.namelist() if n.endswith("SMSSpamCollection")), None)
        if member is None:
            raise RuntimeError("SMSSpamCollection not found inside UCI zip archive.")
        out_path.write_bytes(zf.read(member))

    print(f"Saved {out_path} ({out_path.stat().st_size:,} bytes)")
    return out_path


def uci_to_collection_csv(
    *,
    uci_path: Optional[Path] = None,
    out_path: Optional[Path] = None,
    max_rows: Optional[int] = None,
    spam_only: bool = False,
    ham_only: bool = False,
) -> Path:
    """
    Convert UCI SMSSpamCollection to project collection CSV format.
    Labels: ham -> benign, spam -> smishing.
    feature_notes is set to 'uci_import' for traceability.
    """
    raw = uci_path or (repo_root() / "data" / "raw" / "SMSSpamCollection")
    if not raw.exists():
        raise FileNotFoundError(f"Missing UCI file: {raw}. Run download_uci_sms() first.")

    out = out_path or (repo_root() / "data" / "raw" / "uci_as_collected.csv")
    df = pd.read_csv(raw, sep="\t", header=None, names=["label_raw", "message"], encoding_errors="replace")
    df["label_raw"] = df["label_raw"].astype(str).str.strip().str.lower()

    if spam_only:
        df = df[df["label_raw"] == "spam"]
    elif ham_only:
        df = df[df["label_raw"] == "ham"]

    label_map = {"ham": "benign", "spam": "smishing"}
    unknown = sorted(set(df["label_raw"].unique()) - set(label_map.keys()))
    if unknown:
        raise ValueError(f"Unexpected UCI labels: {unknown}")

    df["label"] = df["label_raw"].map(label_map)
    df["feature_notes"] = "uci_import"
    df = df[["label", "message", "feature_notes"]].dropna(subset=["message"])

    if max_rows is not None:
        df = df.head(int(max_rows))

    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"Wrote {len(df)} UCI rows -> {out}")
    return out
