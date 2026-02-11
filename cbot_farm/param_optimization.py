import math
import random
from itertools import product
from typing import Any, Dict, List, Tuple


def _decimal_places(step: float) -> int:
    text = f"{step:.12f}".rstrip("0")
    if "." not in text:
        return 0
    return len(text.split(".")[1])


def _frange(min_v: float, max_v: float, step: float) -> List[float]:
    values: List[float] = []
    decimals = _decimal_places(step)
    current = min_v
    epsilon = step / 1000.0
    while current <= max_v + epsilon:
        values.append(round(current, decimals))
        current += step
    return values


def _cast(v: float, value_type: str) -> Any:
    if value_type == "int":
        return int(round(v))
    return float(v)


def _values_from_spec(name: str, spec: dict) -> List[Any]:
    value_type = spec.get("type", "float")
    enabled = bool(spec.get("enabled", True))

    if not enabled:
        if "value" not in spec:
            raise ValueError(f"Parameter '{name}' is disabled but has no fixed 'value'")
        return [_cast(float(spec["value"]), value_type)]

    for key in ("min", "max", "step"):
        if key not in spec:
            raise ValueError(f"Parameter '{name}' missing '{key}'")

    min_v = float(spec["min"])
    max_v = float(spec["max"])
    step = float(spec["step"])
    if step <= 0:
        raise ValueError(f"Parameter '{name}' has non-positive step")
    if min_v > max_v:
        raise ValueError(f"Parameter '{name}' has min > max")

    vals = _frange(min_v, max_v, step)
    return [_cast(v, value_type) for v in vals]


def build_param_plan(strategy_id: str, risk_cfg: dict) -> dict:
    optimization_cfg = risk_cfg.get("optimization", {})
    space_cfg = optimization_cfg.get("parameter_space", {}).get(strategy_id)

    if not space_cfg:
        return {
            "source": "strategy_sample",
            "reason": "no parameter_space config for strategy",
            "candidates": [],
            "space": {},
            "total_candidates": 0,
        }

    parameters = space_cfg.get("parameters", {})
    if not parameters:
        return {
            "source": "strategy_sample",
            "reason": "empty parameter_space.parameters",
            "candidates": [],
            "space": {},
            "total_candidates": 0,
        }

    search_mode = space_cfg.get("search_mode", "grid")
    max_combinations = int(space_cfg.get("max_combinations", 5000))
    shuffle = bool(space_cfg.get("shuffle", False))
    seed = int(space_cfg.get("seed", 42))

    names: List[str] = []
    values_by_param: List[List[Any]] = []
    summary: Dict[str, dict] = {}

    for name, spec in parameters.items():
        names.append(name)
        vals = _values_from_spec(name, spec)
        values_by_param.append(vals)
        summary[name] = {
            "enabled": bool(spec.get("enabled", True)),
            "type": spec.get("type", "float"),
            "count": len(vals),
            "min": spec.get("min"),
            "max": spec.get("max"),
            "step": spec.get("step"),
            "value": spec.get("value"),
        }

    raw_total = math.prod(len(v) for v in values_by_param)

    candidates: List[dict] = []
    for combo in product(*values_by_param):
        candidates.append(dict(zip(names, combo)))
        if len(candidates) >= max_combinations:
            break

    if shuffle:
        rnd = random.Random(seed)
        rnd.shuffle(candidates)

    if search_mode == "random":
        # random mode currently means shuffled candidates + sequential draw by iteration.
        pass

    return {
        "source": "parameter_space",
        "reason": "configured",
        "search_mode": search_mode,
        "space": summary,
        "total_candidates": len(candidates),
        "raw_total_candidates": raw_total,
        "truncated": raw_total > len(candidates),
        "candidates": candidates,
    }


def params_for_iteration(iteration: int, plan: dict, fallback_params: dict) -> Tuple[dict, dict]:
    if plan.get("source") != "parameter_space" or not plan.get("candidates"):
        return fallback_params, {
            "source": "strategy_sample",
            "reason": plan.get("reason", "fallback"),
        }

    candidates = plan["candidates"]
    idx = (iteration - 1) % len(candidates)
    return candidates[idx], {
        "source": "parameter_space",
        "candidate_index": idx,
        "total_candidates": len(candidates),
        "search_mode": plan.get("search_mode", "grid"),
        "truncated": bool(plan.get("truncated", False)),
        "raw_total_candidates": int(plan.get("raw_total_candidates", len(candidates))),
    }
