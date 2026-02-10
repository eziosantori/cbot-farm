#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cbot_farm.ingestion import map_instrument

UNIVERSE_PATH = ROOT / "config" / "universe.json"
DATE_FROM = "2024-01-01"
DATE_TO = "2024-01-02"
TEST_TIMEFRAME = "h1"


def load_universe() -> dict:
    with UNIVERSE_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def check_instrument(instrument: str) -> tuple[bool, str]:
    with tempfile.TemporaryDirectory(prefix="cbot-verify-") as tmp_dir:
        cmd = [
            "npx",
            "dukascopy-node",
            "-s",
            "-i",
            instrument,
            "-from",
            DATE_FROM,
            "-to",
            DATE_TO,
            "-t",
            TEST_TIMEFRAME,
            "-f",
            "csv",
            "-dir",
            tmp_dir,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)

    if proc.returncode == 0:
        return True, "ok"

    reason = (proc.stderr or proc.stdout).strip().splitlines()
    return False, reason[-1] if reason else "unknown error"


def main() -> int:
    universe = load_universe()

    failures = []
    checked = 0
    for market, payload in universe.get("markets", {}).items():
        for symbol in payload.get("symbols", []):
            instrument = map_instrument(symbol, market)
            ok, reason = check_instrument(instrument)
            checked += 1
            if not ok:
                failures.append((market, symbol, instrument, reason))
            status = "ok" if ok else "failed"
            print(f"[{status}] market={market} symbol={symbol} instrument={instrument}")

    if failures:
        print("\nInstrument validation failed:\n")
        for market, symbol, instrument, reason in failures:
            print(
                f"- market={market} symbol={symbol} mapped={instrument} reason={reason}"
            )
        return 1

    print(f"\nInstrument validation passed for all {checked} configured symbols.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
