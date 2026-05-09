from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd
from pandas.errors import EmptyDataError


def build_backtest_report(run_dir: Path) -> dict[str, Any]:
    summary = _read_json(run_dir / "summary.json")
    backtests = _read_csv(run_dir / "backtests.csv")
    trade_by_symbol = _read_csv(run_dir / "trade_analysis_by_symbol.csv")

    aggregate = summary.get("aggregate_backtest", {})
    trade_summary = summary.get("trade_analysis_summary", {})
    regime_summary = summary.get("feature_regime_summary", {})
    excess_return = _safe_float(aggregate.get("excess_return"))

    return {
        "run_id": run_dir.name,
        "verdict": _verdict(excess_return),
        "aggregate": aggregate,
        "trade_summary": trade_summary,
        "worst_symbols": _worst_symbols(backtests),
        "best_symbols": _best_symbols(backtests),
        "weak_trade_symbols": _weak_trade_symbols(trade_by_symbol),
        "primary_findings": regime_summary.get("primary_findings", []),
        "decision": _decision(excess_return),
    }


def write_backtest_report_markdown(run_dir: Path, output_path: Path) -> dict[str, Any]:
    report = build_backtest_report(run_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_to_markdown(report), encoding="utf-8")
    return report


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except EmptyDataError:
        return pd.DataFrame()


def _worst_symbols(backtests: pd.DataFrame) -> list[dict[str, Any]]:
    if backtests.empty or "excess_return" not in backtests.columns:
        return []
    data = backtests.copy()
    data["excess_return"] = pd.to_numeric(data["excess_return"], errors="coerce")
    return _records(data.sort_values("excess_return", ascending=True).head(5))


def _best_symbols(backtests: pd.DataFrame) -> list[dict[str, Any]]:
    if backtests.empty or "excess_return" not in backtests.columns:
        return []
    data = backtests.copy()
    data["excess_return"] = pd.to_numeric(data["excess_return"], errors="coerce")
    return _records(data.sort_values("excess_return", ascending=False).head(5))


def _weak_trade_symbols(trade_by_symbol: pd.DataFrame) -> list[dict[str, Any]]:
    if trade_by_symbol.empty or "avg_return_pct" not in trade_by_symbol.columns:
        return []
    data = trade_by_symbol.copy()
    data["avg_return_pct"] = pd.to_numeric(data["avg_return_pct"], errors="coerce")
    return _records(data.sort_values("avg_return_pct", ascending=True).head(5))


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    records = []
    for record in frame.to_dict(orient="records"):
        records.append({key: _json_safe(value) for key, value in record.items()})
    return records


def _verdict(excess_return: float) -> str:
    if math.isnan(excess_return):
        return "insufficient_data"
    if excess_return > 0:
        return "beats_buy_and_hold"
    return "underperforming_buy_and_hold"


def _decision(excess_return: float) -> str:
    if math.isnan(excess_return):
        return "Non promuovere la strategia: dati insufficienti per valutare il backtest."
    if excess_return > 0:
        return "Candidata a ulteriore validazione: batte buy-and-hold nel report corrente."
    return "Non promuovere la strategia: resta sotto buy-and-hold nel report corrente."


def _to_markdown(report: dict[str, Any]) -> str:
    aggregate = report.get("aggregate", {})
    trade_summary = report.get("trade_summary", {})
    lines = [
        "# Backtest Analysis",
        "",
        f"Run: `{report['run_id']}`",
        "",
        "## Verdict",
        "",
        f"- Verdict: `{report['verdict']}`",
        f"- Decisione: {report['decision']}",
        "",
        "## Aggregate",
        "",
        f"- Strategy return: {_format_pct(aggregate.get('strategy_return'))}",
        f"- Buy-and-hold return: {_format_pct(aggregate.get('buy_and_hold_return'))}",
        f"- Excess return: {_format_pct(aggregate.get('excess_return'))}",
        f"- Trades: {aggregate.get('trades', aggregate.get('closed_trades', 'n/a'))}",
        "",
        "## Trade Summary",
        "",
        f"- Total trades: {trade_summary.get('total_trades', 'n/a')}",
        f"- Win rate: {_format_pct(trade_summary.get('win_rate'))}",
        "",
        "## Worst Symbols by Excess Return",
        "",
        *_symbol_lines(report.get("worst_symbols", []), "excess_return"),
        "",
        "## Primary Feature-Regime Findings",
        "",
        *_finding_lines(report.get("primary_findings", [])),
        "",
    ]
    return "\n".join(lines)


def _symbol_lines(records: list[dict[str, Any]], metric: str) -> list[str]:
    if not records:
        return ["- No symbol data available."]
    return [f"- {row.get('symbol', 'n/a')}: {_format_pct(row.get(metric))}" for row in records]


def _finding_lines(findings: list[str]) -> list[str]:
    if not findings:
        return ["- No stable feature-regime finding recorded."]
    return [f"- {finding}" for finding in findings]


def _safe_float(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return number


def _json_safe(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def _format_pct(value: Any) -> str:
    number = _safe_float(value)
    if math.isnan(number):
        return "n/a"
    return f"{number:.2%}"
