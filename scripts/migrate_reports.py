from __future__ import annotations

import argparse
import json
from pathlib import Path

from cbot_farm.config import REPORTS_DIR
from cbot_farm.report_schema import migrate_report_payload


def candidate_paths(reports_root: Path) -> list[Path]:
    paths = [p for p in reports_root.glob("run_*.json") if p.is_file()]
    paths.extend(p for p in (reports_root / "ingest").glob("manifest_*.json") if p.is_file())
    paths.sort()
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate report payloads to the current schema version.")
    parser.add_argument("--write", action="store_true", help="Rewrite files in place instead of running in dry-run mode.")
    args = parser.parse_args()

    migrated = 0
    unchanged = 0
    for path in candidate_paths(REPORTS_DIR):
        with path.open("r", encoding="utf-8") as fh:
            original = json.load(fh)
        updated = migrate_report_payload(original, path=path)

        if updated == original:
            unchanged += 1
            continue

        migrated += 1
        if args.write:
            with path.open("w", encoding="utf-8") as fh:
                json.dump(updated, fh, indent=2)
                fh.write("\n")
        print(f"{'updated' if args.write else 'would update'} {path}")

    mode = "write" if args.write else "dry-run"
    print(f"[{mode}] migrated={migrated} unchanged={unchanged}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
