from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from bots import list_strategies


@dataclass
class ExportResult:
    status: str
    target: str
    strategy_id: Optional[str]
    diagnostics: List[str]
    files: List[str]
    contract: Optional[Dict[str, Any]]


SUPPORTED_EXPORT_PARAMS: Dict[str, List[str]] = {
    "ema_cross_atr": [
        "ema_fast",
        "ema_slow",
        "atr_period",
        "atr_mult_stop",
        "atr_mult_take",
        "rsi_period",
        "rsi_gate",
        "atr_vol_window",
        "atr_vol_ratio_max",
    ],
    "momentum_rider": [
        "ema_fast",
        "ema_slow",
        "macd_fast",
        "macd_slow",
        "macd_signal",
        "rsi_period",
        "rsi_gate",
        "adx_period",
        "min_adx",
        "atr_period",
        "atr_vol_window",
        "atr_vol_ratio_max",
        "atr_mult_stop",
        "atr_mult_take",
    ],
}


EXPECTED_FEATURE_TOKENS: Dict[str, Dict[str, Dict[str, str]]] = {
    "ema_cross_atr": {
        "ctrader": {
            "ema_cross": "currFast > currSlow",
            "rsi_filter": "rsiPrev >= RsiGate",
            "volatility_filter": "atrPrev > atrMean * AtrVolRatioMax",
            "atr_exit": "ExecuteMarketOrder",
        },
        "pine": {
            "ema_cross": "ta.crossover(emaFastValue, emaSlowValue)",
            "rsi_filter": "rsiValue[1] >= rsiGate",
            "volatility_filter": "atrValue[1] <= atrMean[1] * atrVolRatioMax",
            "atr_exit": "strategy.exit(\"Long Exit\"",
        },
    },
    "momentum_rider": {
        "ctrader": {
            "ema_stack": "pricePrev > fastPrev && fastPrev > slowPrev",
            "macd_filter": "macdCurr > signalCurr",
            "adx_filter": "adxPrev < MinAdx",
            "volatility_filter": "atrPrev > atrMean * AtrVolRatioMax",
            "atr_exit": "ExecuteMarketOrder",
        },
        "pine": {
            "ema_stack": "close[1] > emaFastValue[1] and emaFastValue[1] > emaSlowValue[1]",
            "macd_filter": "macdLine > macdSignalValue",
            "adx_filter": "adxValue[1] >= minAdx",
            "volatility_filter": "atrValue[1] <= atrMean[1] * atrVolRatioMax",
            "atr_exit": "strategy.exit(\"Long Exit\"",
        },
    },
}


def _safe_int(params: Dict[str, Any], key: str, default: int) -> int:
    value = params.get(key, default)
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(params: Dict[str, Any], key: str, default: float) -> float:
    value = params.get(key, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _build_contract(campaign: Dict[str, Any]) -> tuple[Optional[Dict[str, Any]], List[str]]:
    diagnostics: List[str] = []
    metadata = campaign.get("metadata", {})

    strategy_id = campaign.get("strategy_id") or metadata.get("strategy_id")
    params = campaign.get("params") or metadata.get("params")
    if not strategy_id:
        diagnostics.append("missing strategy_id in campaign payload")
    if not isinstance(params, dict) or not params:
        diagnostics.append("missing params in campaign payload")

    if diagnostics:
        return None, diagnostics

    display_name = list_strategies().get(str(strategy_id), str(strategy_id))
    contract = {
        "strategy_id": str(strategy_id),
        "display_name": display_name,
        "targets": campaign.get("targets", {}),
        "params": params,
        "gates": campaign.get("gates", {}),
    }
    return contract, diagnostics


def build_contract_from_strategy(
    strategy_id: str,
    params: Dict[str, Any],
    targets: Optional[Dict[str, Any]] = None,
    gates: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    display_name = list_strategies().get(strategy_id, strategy_id)
    return {
        "strategy_id": strategy_id,
        "display_name": display_name,
        "targets": targets or {},
        "params": params,
        "gates": gates or {},
    }


def _render_ctrader_ema_cross_atr(contract: Dict[str, Any]) -> str:
    params = contract["params"]
    return f"""using cAlgo.API;
using cAlgo.API.Indicators;

namespace cAlgo.Robots
{{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class EmaCrossAtrBot : Robot
    {{
        [Parameter("Volume (Units)", DefaultValue = 10000)]
        public int VolumeUnits {{ get; set; }}

        [Parameter("EMA Fast", DefaultValue = {_safe_int(params, "ema_fast", 20)})]
        public int EmaFast {{ get; set; }}

        [Parameter("EMA Slow", DefaultValue = {_safe_int(params, "ema_slow", 50)})]
        public int EmaSlow {{ get; set; }}

        [Parameter("ATR Period", DefaultValue = {_safe_int(params, "atr_period", 14)})]
        public int AtrPeriod {{ get; set; }}

        [Parameter("ATR Stop Mult", DefaultValue = {_safe_float(params, "atr_mult_stop", 1.5)})]
        public double AtrStopMult {{ get; set; }}

        [Parameter("ATR Take Mult", DefaultValue = {_safe_float(params, "atr_mult_take", 2.0)})]
        public double AtrTakeMult {{ get; set; }}

        [Parameter("RSI Period", DefaultValue = {_safe_int(params, "rsi_period", 14)})]
        public int RsiPeriod {{ get; set; }}

        [Parameter("RSI Gate", DefaultValue = {_safe_int(params, "rsi_gate", 55)})]
        public int RsiGate {{ get; set; }}

        [Parameter("ATR Vol Window", DefaultValue = {_safe_int(params, "atr_vol_window", 50)})]
        public int AtrVolWindow {{ get; set; }}

        [Parameter("ATR Vol Ratio Max", DefaultValue = {_safe_float(params, "atr_vol_ratio_max", 1.8)})]
        public double AtrVolRatioMax {{ get; set; }}

        private ExponentialMovingAverage _emaFast;
        private ExponentialMovingAverage _emaSlow;
        private RelativeStrengthIndex _rsi;
        private AverageTrueRange _atr;

        protected override void OnStart()
        {{
            _emaFast = Indicators.ExponentialMovingAverage(Bars.ClosePrices, EmaFast);
            _emaSlow = Indicators.ExponentialMovingAverage(Bars.ClosePrices, EmaSlow);
            _rsi = Indicators.RelativeStrengthIndex(Bars.ClosePrices, RsiPeriod);
            _atr = Indicators.AverageTrueRange(AtrPeriod, MovingAverageType.Exponential);
        }}

        protected override void OnBar()
        {{
            if (Bars.Count < System.Math.Max(EmaSlow, AtrVolWindow) + 2)
                return;

            var i = Bars.Count - 1;
            var prevFast = _emaFast.Result[i - 1];
            var prevSlow = _emaSlow.Result[i - 1];
            var currFast = _emaFast.Result[i];
            var currSlow = _emaSlow.Result[i];
            var rsiPrev = _rsi.Result[i - 1];
            var atrPrev = _atr.Result[i - 1];

            double atrMean = 0.0;
            for (var j = i - AtrVolWindow; j < i; j++)
                atrMean += _atr.Result[j];
            atrMean /= AtrVolWindow;

            if (atrMean <= 0 || atrPrev > atrMean * AtrVolRatioMax)
                return;

            var longSignal = prevFast <= prevSlow && currFast > currSlow && rsiPrev >= RsiGate;
            var shortSignal = prevFast >= prevSlow && currFast < currSlow && rsiPrev <= (100 - RsiGate);

            if (Positions.Count == 0)
            {{
                if (longSignal)
                    OpenTrade(TradeType.Buy, atrPrev);
                else if (shortSignal)
                    OpenTrade(TradeType.Sell, atrPrev);
            }}
        }}

        private void OpenTrade(TradeType tradeType, double atrValue)
        {{
            var stopLossPips = Symbol.NormalizeVolumeInUnits(VolumeUnits) > 0 ? (atrValue * AtrStopMult) / Symbol.PipSize : 0;
            var takeProfitPips = Symbol.NormalizeVolumeInUnits(VolumeUnits) > 0 ? (atrValue * AtrTakeMult) / Symbol.PipSize : 0;
            ExecuteMarketOrder(tradeType, SymbolName, VolumeUnits, "{contract["strategy_id"]}", stopLossPips, takeProfitPips);
        }}
    }}
}}
"""


def _render_pine_ema_cross_atr(contract: Dict[str, Any]) -> str:
    params = contract["params"]
    return f"""//@version=5
strategy("{contract["display_name"]}", overlay=true, initial_capital=10000, pyramiding=0)

emaFast = input.int({_safe_int(params, "ema_fast", 20)}, "EMA Fast")
emaSlow = input.int({_safe_int(params, "ema_slow", 50)}, "EMA Slow")
atrPeriod = input.int({_safe_int(params, "atr_period", 14)}, "ATR Period")
atrStopMult = input.float({_safe_float(params, "atr_mult_stop", 1.5)}, "ATR Stop Mult")
atrTakeMult = input.float({_safe_float(params, "atr_mult_take", 2.0)}, "ATR Take Mult")
rsiPeriod = input.int({_safe_int(params, "rsi_period", 14)}, "RSI Period")
rsiGate = input.int({_safe_int(params, "rsi_gate", 55)}, "RSI Gate")
atrVolWindow = input.int({_safe_int(params, "atr_vol_window", 50)}, "ATR Vol Window")
atrVolRatioMax = input.float({_safe_float(params, "atr_vol_ratio_max", 1.8)}, "ATR Vol Ratio Max")

emaFastValue = ta.ema(close, emaFast)
emaSlowValue = ta.ema(close, emaSlow)
rsiValue = ta.rsi(close, rsiPeriod)
atrValue = ta.atr(atrPeriod)
atrMean = ta.sma(atrValue, atrVolWindow)

volatilityOk = not na(atrMean[1]) and atrValue[1] <= atrMean[1] * atrVolRatioMax
longSignal = ta.crossover(emaFastValue, emaSlowValue) and rsiValue[1] >= rsiGate and volatilityOk
shortSignal = ta.crossunder(emaFastValue, emaSlowValue) and rsiValue[1] <= (100 - rsiGate) and volatilityOk

if strategy.position_size == 0
    if longSignal
        strategy.entry("Long", strategy.long)
    if shortSignal
        strategy.entry("Short", strategy.short)

longStop = strategy.position_avg_price - atrValue * atrStopMult
longTake = strategy.position_avg_price + atrValue * atrTakeMult
shortStop = strategy.position_avg_price + atrValue * atrStopMult
shortTake = strategy.position_avg_price - atrValue * atrTakeMult

strategy.exit("Long Exit", "Long", stop=longStop, limit=longTake)
strategy.exit("Short Exit", "Short", stop=shortStop, limit=shortTake)

plot(emaFastValue, "EMA Fast", color=color.orange)
plot(emaSlowValue, "EMA Slow", color=color.blue)
"""


def _render_ctrader_momentum_rider(contract: Dict[str, Any]) -> str:
    params = contract["params"]
    return f"""using cAlgo.API;
using cAlgo.API.Indicators;

namespace cAlgo.Robots
{{
    [Robot(TimeZone = TimeZones.UTC, AccessRights = AccessRights.None)]
    public class MomentumRider : Robot
    {{
        [Parameter("Volume (Units)", DefaultValue = 10000)]
        public int VolumeUnits {{ get; set; }}

        [Parameter("EMA Fast", DefaultValue = {_safe_int(params, "ema_fast", 15)})]
        public int EmaFast {{ get; set; }}

        [Parameter("EMA Slow", DefaultValue = {_safe_int(params, "ema_slow", 50)})]
        public int EmaSlow {{ get; set; }}

        [Parameter("MACD Fast", DefaultValue = {_safe_int(params, "macd_fast", 12)})]
        public int MacdFast {{ get; set; }}

        [Parameter("MACD Slow", DefaultValue = {_safe_int(params, "macd_slow", 26)})]
        public int MacdSlow {{ get; set; }}

        [Parameter("MACD Signal", DefaultValue = {_safe_int(params, "macd_signal", 9)})]
        public int MacdSignal {{ get; set; }}

        [Parameter("RSI Period", DefaultValue = {_safe_int(params, "rsi_period", 14)})]
        public int RsiPeriod {{ get; set; }}

        [Parameter("RSI Gate", DefaultValue = {_safe_int(params, "rsi_gate", 60)})]
        public int RsiGate {{ get; set; }}

        [Parameter("ADX Period", DefaultValue = {_safe_int(params, "adx_period", 14)})]
        public int AdxPeriod {{ get; set; }}

        [Parameter("Min ADX", DefaultValue = {_safe_int(params, "min_adx", 22)})]
        public int MinAdx {{ get; set; }}

        [Parameter("ATR Period", DefaultValue = {_safe_int(params, "atr_period", 14)})]
        public int AtrPeriod {{ get; set; }}

        [Parameter("ATR Vol Window", DefaultValue = {_safe_int(params, "atr_vol_window", 50)})]
        public int AtrVolWindow {{ get; set; }}

        [Parameter("ATR Vol Ratio Max", DefaultValue = {_safe_float(params, "atr_vol_ratio_max", 1.8)})]
        public double AtrVolRatioMax {{ get; set; }}

        [Parameter("ATR Stop Mult", DefaultValue = {_safe_float(params, "atr_mult_stop", 2.5)})]
        public double AtrStopMult {{ get; set; }}

        [Parameter("ATR Take Mult", DefaultValue = {_safe_float(params, "atr_mult_take", 2.5)})]
        public double AtrTakeMult {{ get; set; }}

        private ExponentialMovingAverage _emaFast;
        private ExponentialMovingAverage _emaSlow;
        private MacdCrossOver _macd;
        private RelativeStrengthIndex _rsi;
        private DirectionalMovementSystem _dms;
        private AverageTrueRange _atr;

        protected override void OnStart()
        {{
            _emaFast = Indicators.ExponentialMovingAverage(Bars.ClosePrices, EmaFast);
            _emaSlow = Indicators.ExponentialMovingAverage(Bars.ClosePrices, EmaSlow);
            _macd = Indicators.MacdCrossOver(MacdLongCycle: MacdSlow, MacdShortCycle: MacdFast, MacdPeriod: MacdSignal);
            _rsi = Indicators.RelativeStrengthIndex(Bars.ClosePrices, RsiPeriod);
            _dms = Indicators.DirectionalMovementSystem(AdxPeriod);
            _atr = Indicators.AverageTrueRange(AtrPeriod, MovingAverageType.Exponential);
        }}

        protected override void OnBar()
        {{
            if (Bars.Count < System.Math.Max(System.Math.Max(EmaSlow, AtrVolWindow), AdxPeriod * 2) + 2)
                return;

            var i = Bars.Count - 1;
            var pricePrev = Bars.ClosePrices[i - 1];
            var fastPrev = _emaFast.Result[i - 1];
            var slowPrev = _emaSlow.Result[i - 1];
            var macdPrev = _macd.Histogram[i - 1] + _macd.Signal[i - 1];
            var signalPrev = _macd.Signal[i - 1];
            var macdCurr = _macd.Histogram[i] + _macd.Signal[i];
            var signalCurr = _macd.Signal[i];
            var histCurr = _macd.Histogram[i];
            var rsiPrev = _rsi.Result[i - 1];
            var adxPrev = _dms.ADX[i - 1];
            var atrPrev = _atr.Result[i - 1];

            double atrMean = 0.0;
            for (var j = i - AtrVolWindow; j < i; j++)
                atrMean += _atr.Result[j];
            atrMean /= AtrVolWindow;

            if (atrMean <= 0 || atrPrev > atrMean * AtrVolRatioMax || adxPrev < MinAdx || Positions.Count > 0)
                return;

            var longSignal =
                pricePrev > fastPrev && fastPrev > slowPrev &&
                macdPrev <= signalPrev && macdCurr > signalCurr &&
                histCurr > 0 && macdCurr > 0 && rsiPrev >= RsiGate;

            var shortSignal =
                pricePrev < fastPrev && fastPrev < slowPrev &&
                macdPrev >= signalPrev && macdCurr < signalCurr &&
                histCurr < 0 && macdCurr < 0 && rsiPrev <= (100 - RsiGate);

            if (longSignal)
                OpenTrade(TradeType.Buy, atrPrev);
            else if (shortSignal)
                OpenTrade(TradeType.Sell, atrPrev);
        }}

        private void OpenTrade(TradeType tradeType, double atrValue)
        {{
            var stopLossPips = Symbol.NormalizeVolumeInUnits(VolumeUnits) > 0 ? (atrValue * AtrStopMult) / Symbol.PipSize : 0;
            var takeProfitPips = Symbol.NormalizeVolumeInUnits(VolumeUnits) > 0 ? (atrValue * AtrTakeMult) / Symbol.PipSize : 0;
            ExecuteMarketOrder(tradeType, SymbolName, VolumeUnits, "{contract["strategy_id"]}", stopLossPips, takeProfitPips);
        }}
    }}
}}
"""


def _render_pine_momentum_rider(contract: Dict[str, Any]) -> str:
    params = contract["params"]
    return f"""//@version=5
strategy("{contract["display_name"]}", overlay=true, initial_capital=10000, pyramiding=0)

emaFast = input.int({_safe_int(params, "ema_fast", 15)}, "EMA Fast")
emaSlow = input.int({_safe_int(params, "ema_slow", 50)}, "EMA Slow")
macdFast = input.int({_safe_int(params, "macd_fast", 12)}, "MACD Fast")
macdSlow = input.int({_safe_int(params, "macd_slow", 26)}, "MACD Slow")
macdSignal = input.int({_safe_int(params, "macd_signal", 9)}, "MACD Signal")
rsiPeriod = input.int({_safe_int(params, "rsi_period", 14)}, "RSI Period")
rsiGate = input.int({_safe_int(params, "rsi_gate", 60)}, "RSI Gate")
adxPeriod = input.int({_safe_int(params, "adx_period", 14)}, "ADX Period")
minAdx = input.int({_safe_int(params, "min_adx", 22)}, "Min ADX")
atrPeriod = input.int({_safe_int(params, "atr_period", 14)}, "ATR Period")
atrVolWindow = input.int({_safe_int(params, "atr_vol_window", 50)}, "ATR Vol Window")
atrVolRatioMax = input.float({_safe_float(params, "atr_vol_ratio_max", 1.8)}, "ATR Vol Ratio Max")
atrStopMult = input.float({_safe_float(params, "atr_mult_stop", 2.5)}, "ATR Stop Mult")
atrTakeMult = input.float({_safe_float(params, "atr_mult_take", 2.5)}, "ATR Take Mult")

emaFastValue = ta.ema(close, emaFast)
emaSlowValue = ta.ema(close, emaSlow)
[macdLine, macdSignalValue, macdHist] = ta.macd(close, macdFast, macdSlow, macdSignal)
rsiValue = ta.rsi(close, rsiPeriod)
atrValue = ta.atr(atrPeriod)
atrMean = ta.sma(atrValue, atrVolWindow)
adxValue = ta.adx(adxPeriod)

volatilityOk = not na(atrMean[1]) and atrValue[1] <= atrMean[1] * atrVolRatioMax
longSignal =
    close[1] > emaFastValue[1] and emaFastValue[1] > emaSlowValue[1] and
    macdLine[1] <= macdSignalValue[1] and macdLine > macdSignalValue and
    macdHist > 0 and macdLine > 0 and
    rsiValue[1] >= rsiGate and adxValue[1] >= minAdx and volatilityOk
shortSignal =
    close[1] < emaFastValue[1] and emaFastValue[1] < emaSlowValue[1] and
    macdLine[1] >= macdSignalValue[1] and macdLine < macdSignalValue and
    macdHist < 0 and macdLine < 0 and
    rsiValue[1] <= (100 - rsiGate) and adxValue[1] >= minAdx and volatilityOk

if strategy.position_size == 0
    if longSignal
        strategy.entry("Long", strategy.long)
    if shortSignal
        strategy.entry("Short", strategy.short)

longStop = strategy.position_avg_price - atrValue * atrStopMult
longTake = strategy.position_avg_price + atrValue * atrTakeMult
shortStop = strategy.position_avg_price + atrValue * atrStopMult
shortTake = strategy.position_avg_price - atrValue * atrTakeMult

strategy.exit("Long Exit", "Long", stop=longStop, limit=longTake)
strategy.exit("Short Exit", "Short", stop=shortStop, limit=shortTake)

plot(emaFastValue, "EMA Fast", color=color.orange)
plot(emaSlowValue, "EMA Slow", color=color.blue)
"""


def _render_code(target: str, contract: Dict[str, Any]) -> Optional[str]:
    strategy_id = str(contract["strategy_id"])
    if strategy_id == "ema_cross_atr":
        return _render_ctrader_ema_cross_atr(contract) if target == "ctrader" else _render_pine_ema_cross_atr(contract)
    if strategy_id == "momentum_rider":
        return _render_ctrader_momentum_rider(contract) if target == "ctrader" else _render_pine_momentum_rider(contract)
    return None


def render_export(target: str, contract: Dict[str, Any]) -> ExportResult:
    strategy_id = str(contract["strategy_id"])
    diagnostics: List[str] = []

    code = _render_code(target=target, contract=contract)
    if code is None:
        diagnostics.append(f"strategy '{strategy_id}' is not supported by exporter v1")
        return ExportResult(
            status="blocked",
            target=target,
            strategy_id=strategy_id,
            diagnostics=diagnostics,
            files=[],
            contract=contract,
        )

    return ExportResult(
        status="generated",
        target=target,
        strategy_id=strategy_id,
        diagnostics=diagnostics,
        files=[],
        contract=contract,
    )


def evaluate_export_parity(target: str, contract: Dict[str, Any]) -> Dict[str, Any]:
    strategy_id = str(contract["strategy_id"])
    params = contract.get("params", {})
    diagnostics: List[str] = []

    code = _render_code(target=target, contract=contract)
    if code is None:
        return {
            "status": "blocked",
            "target": target,
            "strategy_id": strategy_id,
            "diagnostics": [f"strategy '{strategy_id}' is not supported by exporter parity v1"],
            "missing_params": [],
            "unsupported_params": sorted(params.keys()),
            "feature_checks": {},
            "covered_params": [],
        }

    supported_params = SUPPORTED_EXPORT_PARAMS.get(strategy_id, [])
    missing_params = [name for name in supported_params if name not in params]
    unsupported_params = sorted([name for name in params.keys() if name not in supported_params])
    if missing_params:
        diagnostics.append(f"missing contract params: {', '.join(missing_params)}")
    if unsupported_params:
        diagnostics.append(f"unsupported contract params ignored by exporter v1: {', '.join(unsupported_params)}")

    feature_tokens = EXPECTED_FEATURE_TOKENS.get(strategy_id, {}).get(target, {})
    feature_checks = {
        feature: {"token": token, "pass": token in code}
        for feature, token in feature_tokens.items()
    }
    failed_features = [name for name, item in feature_checks.items() if not item["pass"]]
    if failed_features:
        diagnostics.append(f"missing feature tokens: {', '.join(failed_features)}")

    status = "pass" if not missing_params and not failed_features else "fail"
    return {
        "status": status,
        "target": target,
        "strategy_id": strategy_id,
        "diagnostics": diagnostics,
        "missing_params": missing_params,
        "unsupported_params": unsupported_params,
        "covered_params": [name for name in supported_params if name in params],
        "feature_checks": feature_checks,
        "code_preview": code[:400],
    }


def export_campaign_payload(campaign: Dict[str, Any], target: str, out_dir: Path, stamp: str) -> Dict[str, Any]:
    contract, diagnostics = _build_contract(campaign)
    manifest: Dict[str, Any] = {
        "campaign_id": campaign.get("campaign_id"),
        "target": target,
        "requested_at": campaign.get("updated_at"),
        "status": "blocked",
        "diagnostics": diagnostics,
        "files": [],
        "strategy_id": campaign.get("strategy_id") or campaign.get("metadata", {}).get("strategy_id"),
    }

    if contract is None:
        return manifest

    result = render_export(target=target, contract=contract)
    manifest["strategy_id"] = result.strategy_id
    manifest["diagnostics"] = result.diagnostics
    manifest["contract"] = contract
    manifest["status"] = result.status

    if result.status != "generated":
        return manifest

    extension = "cs" if target == "ctrader" else "pine"
    stem = f"{contract['strategy_id']}_{target}_{stamp}"
    code_path = out_dir / f"{stem}.{extension}"

    code = _render_code(target=target, contract=contract)
    if code is None:
        manifest["status"] = "blocked"
        manifest["diagnostics"] = manifest.get("diagnostics", []) + [
            f"strategy '{contract['strategy_id']}' is not supported by exporter v1"
        ]
        return manifest

    code_path.write_text(code, encoding="utf-8")
    manifest["files"] = [code_path.name]
    manifest["parity"] = evaluate_export_parity(target=target, contract=contract)
    return manifest


def write_export_manifest(out_dir: Path, target: str, stamp: str, payload: Dict[str, Any]) -> Path:
    manifest_path = out_dir / f"{target}_export_{stamp}.json"
    manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return manifest_path
