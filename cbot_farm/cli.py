import argparse
from typing import List, Optional

from .pipeline import run_cycle


def _split_csv(value: Optional[str]) -> Optional[List[str]]:
    if not value:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cbot-farm")
    parser.add_argument("--iterations", type=int, default=5)
    parser.add_argument("--skip-ingest", action="store_true")
    parser.add_argument("--ingest-only", action="store_true")
    parser.add_argument("--from-date", default=None, help="Override start date YYYY-MM-DD")
    parser.add_argument("--to-date", default=None, help="Override end date YYYY-MM-DD")
    parser.add_argument(
        "--markets",
        default=None,
        help="Comma-separated market filter (e.g. forex,crypto)",
    )
    parser.add_argument(
        "--symbols",
        default=None,
        help="Comma-separated symbol filter (e.g. EURUSD,BTCUSD)",
    )
    parser.add_argument(
        "--timeframes",
        default=None,
        help="Comma-separated timeframe filter (e.g. 5m,1h)",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    run_cycle(
        iterations=args.iterations,
        skip_ingest=args.skip_ingest,
        from_override=args.from_date,
        to_override=args.to_date,
        ingest_only=args.ingest_only,
        markets_filter=_split_csv(args.markets),
        symbols_filter=_split_csv(args.symbols),
        timeframes_filter=_split_csv(args.timeframes),
    )


if __name__ == "__main__":
    main()
