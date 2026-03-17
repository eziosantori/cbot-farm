import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bots import get_strategy
from cbot_farm.config import REPORTS_DIR, load_configs
from cbot_farm.exporters import build_contract_from_strategy, evaluate_export_parity
from cbot_farm.param_optimization import build_param_plan


def _load_params(strategy_id: str, iteration: int) -> dict:
    _, risk = load_configs()
    plan = build_param_plan(strategy_id=strategy_id, risk_cfg=risk)
    strategy = get_strategy(strategy_id)
    if plan.get("source") == "parameter_space" and plan.get("candidates"):
        idx = max(0, min(iteration - 1, len(plan["candidates"]) - 1))
        return plan["candidates"][idx]
    return strategy.sample_params(iteration)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run exporter parity checks for a supported strategy.")
    parser.add_argument("--strategy", required=True, help="Strategy id (e.g. ema_cross_atr)")
    parser.add_argument("--target", choices=["ctrader", "pine", "all"], default="all")
    parser.add_argument("--iteration", type=int, default=1, help="Parameter-space iteration to inspect")
    parser.add_argument("--params-json", default="", help="Optional JSON object overriding params")
    args = parser.parse_args()

    params = _load_params(strategy_id=args.strategy, iteration=args.iteration)
    if args.params_json:
        params.update(json.loads(args.params_json))

    targets = ["ctrader", "pine"] if args.target == "all" else [args.target]
    contract = build_contract_from_strategy(strategy_id=args.strategy, params=params)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "strategy_id": args.strategy,
        "iteration": args.iteration,
        "params": params,
        "results": [evaluate_export_parity(target=target, contract=contract) for target in targets],
    }

    out_dir = REPORTS_DIR / "parity"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"export_parity_{args.strategy}_{stamp}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"[export-parity] report: {out_path.relative_to(Path.cwd()) if Path.cwd() in out_path.parents else out_path}")
    for result in report["results"]:
        print(
            f"[export-parity] {result['target']}: status={result['status']} "
            f"missing_params={len(result['missing_params'])} "
            f"unsupported_params={len(result['unsupported_params'])}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
