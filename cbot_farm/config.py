import json
from pathlib import Path
from typing import Any, Dict, Tuple


ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"
REPORTS_DIR = ROOT / "reports"


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def load_configs() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    universe = load_json(CONFIG_DIR / "universe.json")
    risk = load_json(CONFIG_DIR / "risk.json")
    return universe, risk
