import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .config import REPORTS_DIR, ROOT


def map_timeframe(tf: str) -> str:
    mapping = {
        "1m": "m1",
        "5m": "m5",
        "15m": "m15",
        "30m": "m30",
        "1h": "h1",
        "4h": "h4",
        "1d": "d1",
    }
    return mapping.get(tf, tf)


def sanitize_symbol(symbol: str) -> str:
    return symbol.replace("/", "").replace("-", "").lower()


def map_instrument(symbol: str, market: Optional[str] = None) -> str:
    normalized = sanitize_symbol(symbol)
    market_key = (market or "").lower()

    # Human-friendly aliases for index symbols.
    index_aliases = {
        "US500": "usa500idxusd",
        "NAS100": "usatechidxusd",
        "GER40": "deuidxeur",
        "UK100": "gbridxgbp",
        "JPN225": "jpnidxjpy",
        "AUS200": "ausidxaud",
    }
    mapped_index = index_aliases.get(symbol.upper())
    if mapped_index:
        return mapped_index

    # Dukascopy equity instruments are usually <ticker>ususd.
    if market_key == "equities" and not normalized.endswith("ususd"):
        return f"{normalized}ususd"

    return normalized


def matches_filter(value: str, values_filter: Optional[Iterable[str]]) -> bool:
    if not values_filter:
        return True
    lookup = {item.lower() for item in values_filter}
    return value.lower() in lookup


def run_dukascopy_download(
    market: str,
    symbol: str,
    timeframe: str,
    date_from: str,
    date_to: str,
    target_dir: Path,
    timeout_seconds: int,
) -> Dict[str, Optional[str]]:
    target_dir.mkdir(parents=True, exist_ok=True)
    instrument = map_instrument(symbol, market)
    dk_timeframe = map_timeframe(timeframe)

    cmd = [
        "npx",
        "dukascopy-node",
        "-i",
        instrument,
        "-from",
        date_from,
        "-to",
        date_to,
        "-t",
        dk_timeframe,
        "-f",
        "csv",
    ]

    try:
        proc = subprocess.run(
            cmd,
            cwd=target_dir,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except FileNotFoundError:
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "status": "failed",
            "reason": "npx not found. Install Node.js/npm first.",
        }
    except subprocess.TimeoutExpired:
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "status": "failed",
            "reason": f"download timeout after {timeout_seconds}s",
        }

    csv_files = sorted(target_dir.rglob("*.csv"), key=lambda p: p.stat().st_mtime)
    latest_file = str(csv_files[-1]) if csv_files else None

    if proc.returncode == 0:
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "status": "ok",
            "command": " ".join(cmd),
            "file": latest_file,
        }

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "status": "failed",
        "command": " ".join(cmd),
        "reason": (proc.stderr or proc.stdout).strip()[-500:],
        "file": latest_file,
    }


def ingest_data(
    universe: dict,
    from_override: Optional[str],
    to_override: Optional[str],
    markets_filter: Optional[List[str]],
    symbols_filter: Optional[List[str]],
    timeframes_filter: Optional[List[str]],
) -> dict:
    source = universe.get("source", {})
    provider = source.get("provider", "")
    if provider != "dukascopy-node":
        return {
            "provider": provider,
            "status": "failed",
            "reason": "unsupported provider configured",
        }

    ingestion_cfg = universe.get("ingestion", {})
    date_from = from_override or ingestion_cfg.get("from", "2024-01-01")
    date_to = to_override or ingestion_cfg.get("to", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    timeout_seconds = int(ingestion_cfg.get("timeout_seconds", 120))
    output_root = ROOT / ingestion_cfg.get("output_dir", "data/dukascopy")

    results = []
    for market, payload in universe.get("markets", {}).items():
        if not matches_filter(market, markets_filter):
            continue

        symbols = payload.get("symbols", [])
        timeframes = payload.get("timeframes", [])
        for symbol in symbols:
            if not matches_filter(symbol, symbols_filter):
                continue
            for timeframe in timeframes:
                if not matches_filter(timeframe, timeframes_filter):
                    continue

                target_dir = output_root / market / sanitize_symbol(symbol) / timeframe
                result = run_dukascopy_download(
                    market=market,
                    symbol=symbol,
                    timeframe=timeframe,
                    date_from=date_from,
                    date_to=date_to,
                    target_dir=target_dir,
                    timeout_seconds=timeout_seconds,
                )
                results.append(result)
                print(f"[ingest] {market} {symbol} {timeframe}: {result['status']}")

    ok_count = sum(1 for item in results if item["status"] == "ok")
    failed_count = len(results) - ok_count
    status = "ok" if failed_count == 0 else ("partial" if ok_count > 0 else "failed")

    manifest = {
        "provider": provider,
        "status": status,
        "from": date_from,
        "to": date_to,
        "summary": {
            "total": len(results),
            "ok": ok_count,
            "failed": failed_count,
        },
        "filters": {
            "markets": markets_filter or [],
            "symbols": symbols_filter or [],
            "timeframes": timeframes_filter or [],
        },
        "results": results,
    }

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    manifests_dir = REPORTS_DIR / "ingest"
    manifests_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifests_dir / f"manifest_{timestamp}.json"
    with manifest_path.open("w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)

    manifest["manifest_path"] = str(manifest_path)
    return manifest
