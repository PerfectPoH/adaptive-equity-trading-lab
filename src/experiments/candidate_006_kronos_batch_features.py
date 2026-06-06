from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from src.experiments.candidate_006_kronos_adapter import normalize_ohlcv_for_kronos
from src.experiments.candidate_006_kronos_smoke import (
    DEFAULT_KRONOS_REPO_DIR,
    _ensure_kronos_repo,
    summarize_kronos_forecast,
)


RUN_ID = "CANDIDATE-006-KRONOS-BATCH-FEATURES-001"
GATE_DIR = Path("experiments/provider_aware_research/candidate_006_kronos_batch_feature_gate_20260606")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs") / RUN_ID
TRADE_LOG = Path("experiments/provider_aware_research/execution_outputs/CANDIDATE-005-RECOVERY-BREADTH-BACKTEST-001/trade_log.csv")
FeaturePredictor = Callable[[pd.DataFrame, int], pd.DataFrame]


def frozen_symbol_date_pairs(trade_log: pd.DataFrame, *, max_pairs: int) -> list[tuple[str, str]]:
    minimal = trade_log[["symbol", "signal_date"]].copy()
    minimal["symbol"] = minimal["symbol"].astype(str)
    minimal["signal_date"] = minimal["signal_date"].astype(str)
    pairs = sorted(set(zip(minimal["symbol"], minimal["signal_date"], strict=False)))
    if len(pairs) > max_pairs:
        raise ValueError(f"Frozen pair count {len(pairs)} exceeds gate max {max_pairs}.")
    return pairs


def run_candidate_006_kronos_batch_feature_generation(
    *,
    gate_dir: Path = GATE_DIR,
    output_dir: Path = OUTPUT_DIR,
    trade_log_path: Path = TRADE_LOG,
    frames: dict[str, pd.DataFrame] | None = None,
    predictor: FeaturePredictor | None = None,
    kronos_repo_dir: Path = DEFAULT_KRONOS_REPO_DIR,
) -> dict[str, Any]:
    gate = _read_json(gate_dir / "gate_manifest.json")
    _validate_gate(gate)
    constraints = gate["runtime_constraints"]
    trade_log = pd.read_csv(trade_log_path)
    pairs = frozen_symbol_date_pairs(trade_log, max_pairs=int(constraints["max_symbol_date_pairs"]))
    provider_query_performed = frames is None
    frames = frames if frames is not None else _load_norgate_frames(sorted({symbol for symbol, _ in pairs}))
    clone_result = {"git_clone_performed": False, "repo_dir": str(kronos_repo_dir)}
    if predictor is None:
        clone_result = _ensure_kronos_repo(kronos_repo_dir)
        predictor = _build_real_predictor(
            kronos_repo_dir=kronos_repo_dir,
            tokenizer_repo=gate["allowed_models"]["tokenizer"],
            model_repo=gate["allowed_models"]["model"],
            device=constraints["device"],
            sample_count=int(constraints["sample_count"]),
            temperature=float(constraints["temperature"]),
            top_p=float(constraints["top_p"]),
        )

    feature_rows: list[dict[str, Any]] = []
    skipped_rows: list[dict[str, Any]] = []
    for symbol, signal_date in pairs:
        frame = frames.get(symbol)
        if frame is None or frame.empty:
            skipped_rows.append({"symbol": symbol, "signal_date": signal_date, "reason": "missing_frame"})
            continue
        prepared = _prepare_asof_frame(frame, signal_date, lookback_rows=int(constraints["lookback_rows"]))
        if prepared is None:
            skipped_rows.append({"symbol": symbol, "signal_date": signal_date, "reason": "insufficient_lookback"})
            continue
        try:
            forecast = predictor(prepared, int(constraints["pred_len"]))
            features = summarize_kronos_forecast(prepared, forecast)
        except Exception as exc:
            skipped_rows.append({"symbol": symbol, "signal_date": signal_date, "reason": f"runtime_error:{str(exc)[:200]}"})
            continue
        feature_rows.append({"symbol": symbol, "as_of_date": signal_date, **features})

    features_frame = pd.DataFrame(feature_rows)
    skipped_frame = pd.DataFrame(skipped_rows)
    coverage = _coverage(pairs, feature_rows)
    blockers = []
    if coverage["feature_rows"] < len(pairs):
        blockers.append("kronos_batch_feature_coverage_incomplete")
    if coverage["feature_rows"] == 0:
        blockers.append("kronos_batch_feature_generation_empty")
    result = {
        "run_id": output_dir.name,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "CANDIDATE_006_KRONOS_BATCH_FEATURE_GENERATION_COMPLETE" if feature_rows else "CANDIDATE_006_KRONOS_BATCH_FEATURE_GENERATION_BLOCKED_EMPTY",
        "linked_gate": str(gate_dir / "gate_manifest.json"),
        "linked_trade_log": str(trade_log_path),
        "provider_query_performed": provider_query_performed,
        "provider_query_scope": "local_norgate_for_frozen_candidate_005_symbols" if provider_query_performed else "injected_test_frames",
        "network_market_data_download_performed": False,
        "git_clone_performed": bool(clone_result.get("git_clone_performed")),
        "clone_result": clone_result,
        "model_download_performed": predictor is not None,
        "new_kronos_inference_performed": predictor is not None,
        "fine_tuning_performed": False,
        "portfolio_backtest_performed": False,
        "threshold_optimization_performed": False,
        "realized_return_input_used": False,
        "promotion_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
        "financial_performance_claimed": False,
        "frozen_pair_count": len(pairs),
        "coverage": coverage,
        "blockers": blockers,
        "next_allowed_action": "Run overlay readiness diagnostic on batch features before any Kronos overlay backtest.",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    features_frame.to_csv(output_dir / "kronos_batch_features.csv", index=False)
    skipped_frame.to_csv(output_dir / "kronos_batch_skipped.csv", index=False)
    _write_json(output_dir / "kronos_batch_feature_result.json", result)
    _write_json(output_dir / "final_decision.json", _final_decision(result))
    (output_dir / "kronos_batch_feature_report.md").write_text(_markdown_report(result), encoding="utf-8")
    return result


def _build_real_predictor(
    *,
    kronos_repo_dir: Path,
    tokenizer_repo: str,
    model_repo: str,
    device: str,
    sample_count: int,
    temperature: float,
    top_p: float,
) -> FeaturePredictor:
    sys.path.insert(0, str(kronos_repo_dir.resolve()))
    from model import Kronos, KronosPredictor, KronosTokenizer  # type: ignore

    tokenizer = KronosTokenizer.from_pretrained(tokenizer_repo)
    model = Kronos.from_pretrained(model_repo)
    kronos_predictor = KronosPredictor(model, tokenizer, device=device, max_context=512)

    def predict(input_frame: pd.DataFrame, pred_len: int) -> pd.DataFrame:
        x_timestamp = pd.Series(input_frame.index)
        y_timestamp = pd.Series(pd.bdate_range(input_frame.index[-1] + pd.Timedelta(days=1), periods=pred_len))
        prediction = kronos_predictor.predict(
            df=input_frame,
            x_timestamp=x_timestamp,
            y_timestamp=y_timestamp,
            pred_len=pred_len,
            T=temperature,
            top_p=top_p,
            sample_count=sample_count,
            verbose=False,
        )
        prediction.index = pd.to_datetime(y_timestamp).dt.tz_localize(None)
        return prediction

    return predict


def _prepare_asof_frame(frame: pd.DataFrame, signal_date: str, *, lookback_rows: int) -> pd.DataFrame | None:
    normalized = normalize_ohlcv_for_kronos(frame)
    asof = pd.Timestamp(signal_date)
    data = normalized[normalized.index <= asof].tail(lookback_rows)
    if len(data) < lookback_rows:
        return None
    return data


def _load_norgate_frames(symbols: list[str]) -> dict[str, pd.DataFrame]:
    import norgatedata

    frames: dict[str, pd.DataFrame] = {}
    for symbol in symbols:
        try:
            frame = norgatedata.price_timeseries(symbol, timeseriesformat="pandas-dataframe")
        except Exception:
            continue
        if frame is None or frame.empty:
            continue
        frame = frame.copy()
        frame.index = pd.to_datetime(frame.index).tz_localize(None).normalize()
        if {"Open", "High", "Low", "Close", "Volume"}.issubset(frame.columns):
            frames[symbol] = frame.sort_index()
    return frames


def _coverage(pairs: list[tuple[str, str]], feature_rows: list[dict[str, Any]]) -> dict[str, Any]:
    feature_pairs = {(str(row["symbol"]), str(row["as_of_date"])) for row in feature_rows}
    pair_set = set(pairs)
    feature_symbols = {symbol for symbol, _ in feature_pairs}
    trade_symbols = {symbol for symbol, _ in pair_set}
    feature_dates = {date for _, date in feature_pairs}
    trade_dates = {date for _, date in pair_set}
    return {
        "frozen_pairs": len(pair_set),
        "feature_rows": len(feature_rows),
        "pair_coverage_ratio": float(len(pair_set & feature_pairs) / len(pair_set)) if pair_set else 0.0,
        "unique_trade_symbols": len(trade_symbols),
        "unique_feature_symbols": len(feature_symbols),
        "symbol_coverage_ratio": float(len(trade_symbols & feature_symbols) / len(trade_symbols)) if trade_symbols else 0.0,
        "unique_trade_dates": len(trade_dates),
        "unique_feature_dates": len(feature_dates),
        "date_coverage_ratio": float(len(trade_dates & feature_dates) / len(trade_dates)) if trade_dates else 0.0,
    }


def _validate_gate(gate: dict[str, Any]) -> None:
    if gate.get("status") != "APPROVED_KRONOS_BATCH_FEATURE_GENERATION_ONLY":
        raise RuntimeError("Kronos batch feature gate is not approved.")
    for key in ("promotion_allowed", "paper_trading_allowed", "live_trading_allowed"):
        if gate.get(key):
            raise RuntimeError(f"Gate unexpectedly allows {key}.")


def _final_decision(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": result["decision"],
        "provider_query_performed": result["provider_query_performed"],
        "network_market_data_download_performed": False,
        "new_kronos_inference_performed": result["new_kronos_inference_performed"],
        "portfolio_backtest_performed": False,
        "threshold_optimization_performed": False,
        "realized_return_input_used": False,
        "promotion_allowed": False,
        "blockers": result["blockers"],
        "next_allowed_action": result["next_allowed_action"],
    }


def _markdown_report(result: dict[str, Any]) -> str:
    coverage = result["coverage"]
    lines = [
        "# Candidate 006 Kronos Batch Features 001",
        "",
        f"Decision: `{result['decision']}`",
        "",
        "Scope: batch feature generation only. No realized-return input, no reranking, no backtest, no promotion.",
        "",
        "## Coverage",
        "",
        f"- Frozen pairs: `{coverage['frozen_pairs']}`",
        f"- Feature rows: `{coverage['feature_rows']}`",
        f"- Pair coverage ratio: `{coverage['pair_coverage_ratio']}`",
        f"- Symbol coverage ratio: `{coverage['symbol_coverage_ratio']}`",
        f"- Date coverage ratio: `{coverage['date_coverage_ratio']}`",
        "",
        "## Controls",
        "",
        f"- Provider query performed: `{result['provider_query_performed']}`",
        f"- Network market-data download performed: `{result['network_market_data_download_performed']}`",
        f"- Portfolio backtest performed: `{result['portfolio_backtest_performed']}`",
        f"- Threshold optimization performed: `{result['threshold_optimization_performed']}`",
        f"- Realized-return input used: `{result['realized_return_input_used']}`",
        "",
        "## Blockers",
        "",
    ]
    if result["blockers"]:
        for blocker in result["blockers"]:
            lines.append(f"- `{blocker}`")
    else:
        lines.append("- None for feature generation. Overlay readiness must still be rerun before backtesting.")
    lines.extend(["", "## Next Allowed Action", "", f"`{result['next_allowed_action']}`", ""])
    return "\n".join(lines)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    run_candidate_006_kronos_batch_feature_generation()
