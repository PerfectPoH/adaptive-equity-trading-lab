from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from src.experiments.candidate_006_kronos_adapter import normalize_ohlcv_for_kronos


RUN_ID = "CANDIDATE-006-KRONOS-INFERENCE-SMOKE-001"
GATE_DIR = Path("experiments/provider_aware_research/candidate_006_kronos_inference_smoke_gate_20260602")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs") / RUN_ID
KRONOS_REPO_URL = "https://github.com/shiyu-coder/Kronos.git"
DEFAULT_KRONOS_REPO_DIR = Path(".external/kronos")
DEFAULT_SNAPSHOT = Path("data/snapshots/SPY_2026-05-09.csv")
KRONOS_SMOKE_FEATURES = [
    "kronos_forecast_return_mean",
    "kronos_forecast_return_median",
    "kronos_forecast_return_std",
    "kronos_probability_up",
    "kronos_forecast_drawdown_proxy",
    "kronos_sample_path_agreement",
]


def prepare_kronos_input_frame(frame: pd.DataFrame, *, lookback_rows: int) -> pd.DataFrame:
    normalized = normalize_ohlcv_for_kronos(frame)
    if len(normalized) < lookback_rows:
        raise ValueError(f"Kronos smoke requires at least {lookback_rows} rows; got {len(normalized)}.")
    return normalized.tail(lookback_rows)


def summarize_kronos_forecast(input_frame: pd.DataFrame, forecast_frame: pd.DataFrame) -> dict[str, float]:
    forecast = normalize_ohlcv_for_kronos(forecast_frame)
    last_close = float(input_frame["close"].iloc[-1])
    close_returns = forecast["close"].astype(float) / last_close - 1.0
    step_returns = forecast["close"].astype(float).pct_change().dropna()
    path_sign = (close_returns > 0).astype(float)
    return {
        "kronos_forecast_return_mean": float(close_returns.mean()),
        "kronos_forecast_return_median": float(close_returns.median()),
        "kronos_forecast_return_std": float(step_returns.std(ddof=0)) if len(step_returns) else 0.0,
        "kronos_probability_up": float(path_sign.mean()) if len(path_sign) else 0.0,
        "kronos_forecast_drawdown_proxy": float(forecast["low"].astype(float).min() / last_close - 1.0),
        "kronos_sample_path_agreement": float(max(path_sign.mean(), 1.0 - path_sign.mean())) if len(path_sign) else 0.0,
    }


def run_candidate_006_kronos_inference_smoke(
    *,
    gate_dir: Path = GATE_DIR,
    output_dir: Path = OUTPUT_DIR,
    sample_frame: pd.DataFrame | None = None,
    kronos_repo_dir: Path = DEFAULT_KRONOS_REPO_DIR,
) -> dict[str, Any]:
    gate = _read_json(gate_dir / "gate_manifest.json")
    _validate_gate(gate)
    constraints = gate["runtime_constraints"]
    lookback_rows = int(constraints["lookback_rows"])
    pred_len = int(constraints["pred_len"])
    input_frame = prepare_kronos_input_frame(
        sample_frame if sample_frame is not None else _load_default_sample(),
        lookback_rows=lookback_rows,
    )

    clone_result = _ensure_kronos_repo(kronos_repo_dir)
    result: dict[str, Any]
    try:
        forecast = _run_real_kronos_prediction(
            input_frame=input_frame,
            pred_len=pred_len,
            kronos_repo_dir=kronos_repo_dir,
            tokenizer_repo=gate["allowed_models"]["tokenizer"],
            model_repo=gate["allowed_models"]["model"],
            device=constraints["device"],
            sample_count=int(constraints["sample_count"]),
            temperature=float(constraints["temperature"]),
            top_p=float(constraints["top_p"]),
        )
        features = summarize_kronos_forecast(input_frame, forecast)
        result = _base_result(gate, clone_result)
        result.update(
            {
                "decision": "CANDIDATE_006_KRONOS_INFERENCE_SMOKE_COMPLETE_NO_BACKTEST",
                "inference_performed": True,
                "model_download_performed": True,
                "input_rows": int(len(input_frame)),
                "forecast_rows": int(len(forecast)),
                "feature_summary": features,
                "blockers": [],
            }
        )
        output_dir.mkdir(parents=True, exist_ok=True)
        forecast.to_csv(output_dir / "forecast_preview.csv", index_label="timestamp")
    except Exception as exc:
        result = _base_result(gate, clone_result)
        result.update(
            {
                "decision": "CANDIDATE_006_KRONOS_INFERENCE_SMOKE_BLOCKED_RUNTIME_ERROR",
                "inference_performed": False,
                "model_download_performed": True,
                "input_rows": int(len(input_frame)),
                "forecast_rows": 0,
                "feature_summary": {},
                "blockers": ["kronos_runtime_error"],
                "runtime_error": str(exc)[:1000],
            }
        )
        output_dir.mkdir(parents=True, exist_ok=True)

    _write_json(output_dir / "kronos_smoke_result.json", result)
    _write_json(output_dir / "final_decision.json", _final_decision(result))
    (output_dir / "kronos_smoke_report.md").write_text(_markdown_report(result), encoding="utf-8")
    return result


def _run_real_kronos_prediction(
    *,
    input_frame: pd.DataFrame,
    pred_len: int,
    kronos_repo_dir: Path,
    tokenizer_repo: str,
    model_repo: str,
    device: str,
    sample_count: int,
    temperature: float,
    top_p: float,
) -> pd.DataFrame:
    sys.path.insert(0, str(kronos_repo_dir.resolve()))
    from model import Kronos, KronosPredictor, KronosTokenizer  # type: ignore

    tokenizer = KronosTokenizer.from_pretrained(tokenizer_repo)
    model = Kronos.from_pretrained(model_repo)
    predictor = KronosPredictor(model, tokenizer, device=device, max_context=512)
    x_timestamp = pd.Series(input_frame.index)
    y_timestamp = pd.Series(pd.bdate_range(input_frame.index[-1] + pd.Timedelta(days=1), periods=pred_len))
    prediction = predictor.predict(
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


def _ensure_kronos_repo(kronos_repo_dir: Path) -> dict[str, Any]:
    if (kronos_repo_dir / ".git").is_dir():
        return {"git_clone_performed": False, "repo_dir": str(kronos_repo_dir)}
    kronos_repo_dir.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        ["git", "clone", "--depth", "1", KRONOS_REPO_URL, str(kronos_repo_dir)],
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    return {
        "git_clone_performed": proc.returncode == 0,
        "repo_dir": str(kronos_repo_dir),
        "returncode": proc.returncode,
        "stderr": proc.stderr.strip()[:500],
    }


def _load_default_sample() -> pd.DataFrame:
    if not DEFAULT_SNAPSHOT.is_file():
        return _synthetic_sample()
    frame = pd.read_csv(DEFAULT_SNAPSHOT)
    frame["Date"] = pd.to_datetime(frame["Date"])
    frame = frame.set_index("Date")
    return frame[["Open", "High", "Low", "Close", "Volume"]]


def _synthetic_sample() -> pd.DataFrame:
    index = pd.bdate_range("2026-01-01", periods=40)
    return pd.DataFrame(
        {
            "Open": [100.0 + i * 0.05 for i in range(40)],
            "High": [100.3 + i * 0.05 for i in range(40)],
            "Low": [99.8 + i * 0.05 for i in range(40)],
            "Close": [100.1 + i * 0.05 for i in range(40)],
            "Volume": [1_000_000 + i * 1000 for i in range(40)],
        },
        index=index,
    )


def _base_result(gate: dict[str, Any], clone_result: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "linked_gate": str(GATE_DIR / "gate_manifest.json"),
        "git_clone_performed": bool(clone_result.get("git_clone_performed")),
        "clone_result": clone_result,
        "provider_query_performed": False,
        "market_data_download_performed": False,
        "fine_tuning_performed": False,
        "portfolio_backtest_performed": False,
        "parameter_sweep_performed": False,
        "signal_generation_performed": False,
        "promotion_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
        "financial_performance_claimed": False,
        "model_repos": gate["allowed_models"],
        "runtime_constraints": gate["runtime_constraints"],
        "next_allowed_action": "Archive smoke result, then create a separate Kronos overlay feature gate before any portfolio connection.",
    }


def _validate_gate(gate: dict[str, Any]) -> None:
    if gate.get("status") != "APPROVED_KRONOS_INFERENCE_SMOKE_ONLY":
        raise RuntimeError("Candidate 006 Kronos inference smoke gate is not approved.")
    for key in ["promotion_allowed", "paper_trading_allowed", "live_trading_allowed"]:
        if gate.get(key):
            raise RuntimeError(f"Gate unexpectedly allows {key}.")


def _final_decision(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": result["decision"],
        "git_clone_performed": result["git_clone_performed"],
        "model_download_performed": result["model_download_performed"],
        "inference_performed": result["inference_performed"],
        "portfolio_backtest_performed": False,
        "promotion_allowed": False,
        "blockers": result["blockers"],
        "next_allowed_action": result["next_allowed_action"],
    }


def _markdown_report(result: dict[str, Any]) -> str:
    lines = [
        "# Candidate 006 Kronos Inference Smoke 001",
        "",
        f"Decision: `{result['decision']}`",
        "",
        "Scope: one CPU inference smoke only. No backtest, no signal generation, no promotion.",
        "",
        "## Controls",
        "",
        f"- Git clone performed: `{result['git_clone_performed']}`",
        f"- Model download performed: `{result['model_download_performed']}`",
        f"- Inference performed: `{result['inference_performed']}`",
        f"- Portfolio backtest performed: `{result['portfolio_backtest_performed']}`",
        f"- Promotion allowed: `{result['promotion_allowed']}`",
        f"- Financial performance claimed: `{result['financial_performance_claimed']}`",
        "",
        "## Feature Summary",
        "",
    ]
    if result.get("feature_summary"):
        for key in KRONOS_SMOKE_FEATURES:
            lines.append(f"- `{key}`: `{result['feature_summary'].get(key)}`")
    else:
        lines.append("- No feature summary produced.")
    if result.get("blockers"):
        lines.extend(["", "## Blockers", ""])
        for blocker in result["blockers"]:
            lines.append(f"- `{blocker}`")
        if result.get("runtime_error"):
            lines.append(f"- Runtime error: `{result['runtime_error']}`")
    lines.extend(["", "## Next Allowed Action", "", f"`{result['next_allowed_action']}`", ""])
    return "\n".join(lines)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    run_candidate_006_kronos_inference_smoke()
