from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.data_collection.download_public import download_uci_sms, uci_to_collection_csv


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Download public SMS datasets for the smishing research pipeline."
    )
    parser.add_argument(
        "--uci",
        action="store_true",
        help="Download UCI SMS Spam Collection to data/raw/SMSSpamCollection",
    )
    parser.add_argument(
        "--uci-to-collected",
        action="store_true",
        help="Also convert UCI file to data/raw/uci_as_collected.csv (Dataset1 format)",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=None,
        help="Limit rows when converting UCI to collection CSV",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if the raw file already exists",
    )
    args = parser.parse_args(argv)

    if not args.uci and not args.uci_to_collected:
        parser.error("Pick at least one of --uci or --uci-to-collected.")

    uci_path = None
    if args.uci or args.uci_to_collected:
        uci_path = download_uci_sms(force=args.force)

    if args.uci_to_collected:
        uci_to_collection_csv(uci_path=uci_path, max_rows=args.max_rows)

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
