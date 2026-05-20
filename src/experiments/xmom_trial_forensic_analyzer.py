from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


REQUIRED_COLUMNS = {
    "symbol",
    "signal_date",
    "entry_date",
    "exit_date",
    "position_notional",
    "pnl",
    "return_pct",
    "momentum_3m",
    "momentum_6m",
    "momentum_12m",
    "rank_aggregate_score",
    "avg_dollar_volume_20d",
    "rolling_volatility_20d",
    "participation_rate",
    "impact_bps",
}


def analyze_xmom_trial_forensics(run_dir: str | Path, top_n: int = 3) -> dict[str, Any]:
    run_path = Path(run_dir)
    trade_log_path = run_path / "portfolio_trade_log.csv"
    if not trade_log_path.exists():
        raise FileNotFoundError(trade_log_path)

    trades = pd.read_csv(trade_log_path)
    missing = sorted(REQUIRED_COLUMNS - set(trades.columns))
    if missing:
        raise ValueError(f"portfolio_trade_log.csv missing required columns: {missing}")
    if trades.empty:
        raise ValueError("portfolio_trade_log.csv is empty")

    numeric_columns = [
        "position_notional",
        "pnl",
        "return_pct",
        "momentum_3m",
        "momentum_6m",
        "momentum_12m",
        "rank_aggregate_score",
        "avg_dollar_volume_20d",
        "rolling_volatility_20d",
        "participation_rate",
        "impact_bps",
    ]
    for column in numeric_columns:
        trades[column] = pd.to_numeric(trades[column], errors="coerce")

    sorted_trades = trades.sort_values("pnl", ascending=False).reset_index(drop=True)
    top = sorted_trades.head(top_n).copy()
    rest = sorted_trades.iloc[top_n:].copy()
    total_pnl = float(trades["pnl"].sum())
    top_pnl = float(top["pnl"].sum())
    rest_pnl = float(rest["pnl"].sum()) if not rest.empty else 0.0

    symbol_summary = (
        trades.groupby("symbol", dropna=False)
        .agg(
            trades=("symbol", "size"),
            total_pnl=("pnl", "sum"),
            avg_return_pct=("return_pct", "mean"),
            avg_rank_score=("rank_aggregate_score", "mean"),
            avg_volatility_20d=("rolling_volatility_20d", "mean"),
            avg_dollar_volume_20d=("avg_dollar_volume_20d", "mean"),
        )
        .reset_index()
        .sort_values("total_pnl", ascending=False)
    )

    loser_frame = trades[trades["pnl"] < 0]
    winner_frame = trades[trades["pnl"] > 0]
    report = {
        "run_dir": str(run_path),
        "total_trades": int(len(trades)),
        "winner_count": int(len(winner_frame)),
        "loser_count": int(len(loser_frame)),
        "total_pnl": total_pnl,
        "top_n": int(top_n),
        "top_n_pnl": top_pnl,
        "rest_pnl": rest_pnl,
        "top_n_contribution_pct": _safe_ratio(top_pnl, total_pnl),
        "sign_flip_excluding_top_n": rest_pnl < 0 < total_pnl,
        "symbol_concentration": symbol_summary.to_dict(orient="records"),
        "top_trades": _records(top),
        "loser_diagnostics": _diagnostics(loser_frame),
        "winner_diagnostics": _diagnostics(winner_frame),
        "interpretation": _interpretation(total_pnl, rest_pnl, top_pnl, len(trades), len(top)),
    }
    return report


def write_forensic_artifacts(run_dir: str | Path, top_n: int = 3) -> dict[str, Path]:
    run_path = Path(run_dir)
    report = analyze_xmom_trial_forensics(run_path, top_n=top_n)
    trade_log = pd.read_csv(run_path / "portfolio_trade_log.csv").sort_values("pnl", ascending=False)
    top = trade_log.head(top_n)
    rest = trade_log.iloc[top_n:]

    json_path = run_path / "trade_forensics_report.json"
    top_path = run_path / "trade_forensics_top_trades.csv"
    rest_path = run_path / "trade_forensics_non_top_trades.csv"
    md_path = run_path / "trade_forensics_report.md"

    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    top.to_csv(top_path, index=False)
    rest.to_csv(rest_path, index=False)
    md_path.write_text(_markdown(report), encoding="utf-8")
    return {"json": json_path, "top_trades": top_path, "non_top_trades": rest_path, "markdown": md_path}


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    artifacts = write_forensic_artifacts(args.run_dir, top_n=args.top_n)
    print(json.dumps({name: str(path) for name, path in artifacts.items()}, indent=2, sort_keys=True))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create an independent forensic report for the completed XMOM trial.")
    parser.add_argument("--run-dir", required=True, help="Completed XMOM run artifact directory.")
    parser.add_argument("--top-n", type=int, default=3, help="Number of top winners to isolate.")
    return parser


def _diagnostics(frame: pd.DataFrame) -> dict[str, float | int | None]:
    if frame.empty:
        return {
            "count": 0,
            "avg_return_pct": None,
            "avg_rank_score": None,
            "avg_volatility_20d": None,
            "avg_participation_rate": None,
            "avg_impact_bps": None,
        }
    return {
        "count": int(len(frame)),
        "avg_return_pct": float(frame["return_pct"].mean()),
        "avg_rank_score": float(frame["rank_aggregate_score"].mean()),
        "avg_volatility_20d": float(frame["rolling_volatility_20d"].mean()),
        "avg_participation_rate": float(frame["participation_rate"].mean()),
        "avg_impact_bps": float(frame["impact_bps"].mean()),
    }


def _interpretation(total_pnl: float, rest_pnl: float, top_pnl: float, total_trades: int, top_n: int) -> str:
    if total_pnl > 0 and rest_pnl < 0:
        return (
            f"Positive headline P&L is concentrated in the top {top_n} trades. "
            f"The remaining {total_trades - top_n} trades are negative, so this is forensic evidence, not a promotable edge."
        )
    if total_pnl > 0 and rest_pnl >= 0:
        return "Positive P&L survives top-trade removal; still requires separate preregistered replication before promotion."
    if top_pnl > 0:
        return "Top trades are positive but insufficient to rescue the full run."
    return "No positive top-trade concentration detected."


def _safe_ratio(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return float(numerator / denominator)


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    columns = [
        "symbol",
        "signal_date",
        "entry_date",
        "exit_date",
        "pnl",
        "return_pct",
        "rank_aggregate_score",
        "momentum_3m",
        "momentum_6m",
        "momentum_12m",
        "avg_dollar_volume_20d",
        "rolling_volatility_20d",
    ]
    return frame[columns].to_dict(orient="records")


def _markdown(report: dict[str, Any]) -> str:
    top_rows = "\n".join(
        "- {symbol} {entry_date}->{exit_date}: pnl={pnl:.2f}, return={return_pct:.2%}, rank={rank_aggregate_score:.4f}".format(
            **row
        )
        for row in report["top_trades"]
    )
    symbols = "\n".join(
        "- {symbol}: trades={trades}, total_pnl={total_pnl:.2f}, avg_return={avg_return_pct:.2%}".format(**row)
        for row in report["symbol_concentration"]
    )
    return "\n".join(
        [
            "# XMOM Trial 001 Trade Forensics",
            "",
            "## Summary",
            "",
            f"- total_trades: {report['total_trades']}",
            f"- winner_count: {report['winner_count']}",
            f"- loser_count: {report['loser_count']}",
            f"- total_pnl: {report['total_pnl']:.2f}",
            f"- top_{report['top_n']}_pnl: {report['top_n_pnl']:.2f}",
            f"- rest_pnl: {report['rest_pnl']:.2f}",
            f"- top_{report['top_n']}_contribution_pct: {report['top_n_contribution_pct']:.2%}",
            f"- sign_flip_excluding_top_{report['top_n']}: {report['sign_flip_excluding_top_n']}",
            "",
            "## Top Trades",
            "",
            top_rows,
            "",
            "## Symbol Concentration",
            "",
            symbols,
            "",
            "## Interpretation",
            "",
            str(report["interpretation"]),
            "",
            "No paper/live trading or strategy promotion is authorized by this forensic report.",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
