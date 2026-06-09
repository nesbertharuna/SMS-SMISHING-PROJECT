from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

# Allow running as `python scripts/collect_sms.py` from repo root.
_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.data_collection.collector import SmsCollector, collection_stats, default_collection_path
from scripts.data_collection.schema import FEATURE_NOTE_EXAMPLES, VALID_LABELS


def _prompt(label: str) -> str:
    value = input(f"{label}: ").strip()
    if not value:
        raise ValueError(f"{label} is required.")
    return value


def cmd_add(args: argparse.Namespace) -> int:
    collector = SmsCollector(args.file)

    if args.label and args.message:
        row = collector.add_sample(
            label=args.label,
            message=args.message,
            feature_notes=args.feature_notes or "",
        )
        collector.write_audit_log("add", {"row": row})
        print("Added:", json.dumps(row, ensure_ascii=False))
        return 0

    print("Interactive SMS collection (Ctrl+C to stop)\n")
    print(f"Labels: {', '.join(sorted(VALID_LABELS))}")
    print(f"Example feature_notes: {', '.join(FEATURE_NOTE_EXAMPLES[:6])}, ...\n")

    count = 0
    while True:
        try:
            label = _prompt("label (benign/smishing)")
            message = _prompt("message")
            feature_notes = input("feature_notes (optional): ").strip()
            row = collector.add_sample(label=label, message=message, feature_notes=feature_notes)
            collector.write_audit_log("add_interactive", {"row": row})
            count += 1
            print(f"Saved sample #{count}\n")
            again = input("Add another? [Y/n]: ").strip().lower()
            if again in {"n", "no"}:
                break
        except (KeyboardInterrupt, EOFError):
            print("\nStopped.")
            break
        except ValueError as exc:
            print(f"Error: {exc}\n")

    stats = collection_stats(collector.load())
    print("Collection stats:", json.dumps(stats, indent=2))
    print(f"File: {collector.path}")
    return 0


def cmd_import(args: argparse.Namespace) -> int:
    collector = SmsCollector(args.file)
    path = Path(args.input)
    if not path.exists():
        raise FileNotFoundError(path)

    if path.suffix.lower() == ".jsonl":
        added = collector.add_from_jsonl(path)
    else:
        added = collector.add_from_csv(path)

    removed = collector.dedupe() if args.dedupe else 0
    collector.write_audit_log("import", {"input": str(path), "added": added, "deduped": removed})
    print(f"Imported {added} row(s) from {path}")
    if removed:
        print(f"Removed {removed} exact duplicate row(s)")
    print("Stats:", json.dumps(collection_stats(collector.load()), indent=2))
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    collector = SmsCollector(args.file)
    df = collector.load()
    print(json.dumps(collection_stats(df), indent=2))
    print(f"File: {collector.path} ({'exists' if collector.path.exists() else 'missing'})")
    if args.show and not df.empty:
        print(df.tail(min(args.show, len(df))).to_string(index=False))
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    collector = SmsCollector(args.file)
    out = collector.export_dataset1(args.out, dedupe_messages=not args.keep_duplicates)
    collector.write_audit_log("export", {"out": str(out)})
    print(f"Exported -> {out}")
    print("Stats:", json.dumps(collection_stats(collector.load()), indent=2))
    return 0


def cmd_dedupe(args: argparse.Namespace) -> int:
    collector = SmsCollector(args.file)
    removed = collector.dedupe(keep=args.keep)
    print(f"Removed {removed} exact duplicate row(s)")
    print("Stats:", json.dumps(collection_stats(collector.load()), indent=2))
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Collect labelled SMS samples for Dataset1 (benign vs smishing)."
    )
    parser.add_argument(
        "--file",
        default=str(default_collection_path()),
        help="Collection CSV path (default: data/raw/collected_sms.csv)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Add one sample (interactive or via flags)")
    p_add.add_argument("--label", choices=sorted(VALID_LABELS))
    p_add.add_argument("--message")
    p_add.add_argument("--feature-notes", default="")
    p_add.set_defaults(func=cmd_add)

    p_import = sub.add_parser("import", help="Import CSV or JSONL batch file")
    p_import.add_argument("input", help="Path to .csv or .jsonl file")
    p_import.add_argument("--dedupe", action="store_true", help="Remove exact duplicates after import")
    p_import.set_defaults(func=cmd_import)

    p_stats = sub.add_parser("stats", help="Show collection statistics")
    p_stats.add_argument("--show", type=int, default=0, help="Print last N rows")
    p_stats.set_defaults(func=cmd_stats)

    p_export = sub.add_parser("export", help="Export to Dataset1.csv format")
    p_export.add_argument(
        "--out",
        default=str(Path("ml-backend") / "dataset" / "Dataset1.csv"),
        help="Output Dataset1 path",
    )
    p_export.add_argument(
        "--keep-duplicates",
        action="store_true",
        help="Keep multiple rows with the same message text",
    )
    p_export.set_defaults(func=cmd_export)

    p_dedupe = sub.add_parser("dedupe", help="Remove exact duplicate rows")
    p_dedupe.add_argument("--keep", choices=("first", "last"), default="last")
    p_dedupe.set_defaults(func=cmd_dedupe)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
