from __future__ import annotations

from typing import Any

import pandas as pd


DEFAULT_THRESHOLDS = [
    0.15,
    0.20,
    0.25,
    0.30,
    0.35,
    0.40,
    0.45,
    0.50,
    0.55,
    0.60,
    0.65,
    0.70,
    0.75,
]


def build_threshold_diagnostics(
    signals: pd.DataFrame,
    thresholds: list[float] | None = None,
    min_scanner_score: float = 70,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    thresholds = thresholds or DEFAULT_THRESHOLDS
    frames = [
        _period_threshold_diagnostics(signals, "validation", "2023-01-01", "2023-12-31", thresholds, min_scanner_score),
        _period_threshold_diagnostics(signals, "test", "2024-01-01", "2024-12-31", thresholds, min_scanner_score),
    ]
    diagnostics = pd.concat(frames, ignore_index=True)
    return diagnostics, summarize_threshold_diagnostics(diagnostics)


def summarize_threshold_diagnostics(diagnostics: pd.DataFrame, min_validation_signals: int = 20) -> dict[str, Any]:
    validation = diagnostics[diagnostics["period"] == "validation"].copy()
    if validation.empty:
        return {"recommended_threshold": None, "reason": "No validation diagnostics available"}

    viable = validation[validation["signal_days"] >= min_validation_signals].copy()
    if viable.empty:
        viable = validation.copy()
        reason = "No threshold met the minimum validation signal count; selected highest validation success rate anyway."
    else:
        reason = "Selected highest validation success rate among thresholds with enough validation signals."

    viable = viable.sort_values(
        ["label_success_rate", "signal_days", "symbols_with_signals"],
        ascending=[False, False, False],
    )
    best = viable.iloc[0]
    return {
        "recommended_threshold": float(best["threshold"]),
        "validation_signal_days": int(best["signal_days"]),
        "validation_success_rate": _safe_float(best["label_success_rate"]),
        "validation_symbols_with_signals": int(best["symbols_with_signals"]),
        "reason": reason,
    }


def _period_threshold_diagnostics(
    signals: pd.DataFrame,
    period: str,
    start: str,
    end: str,
    thresholds: list[float],
    min_scanner_score: float,
) -> pd.DataFrame:
    dates = pd.to_datetime(signals.index)
    rows = signals.loc[(dates >= pd.Timestamp(start)) & (dates <= pd.Timestamp(end))].copy()
    scanner_score = pd.to_numeric(rows.get("scanner_score"), errors="coerce")
    probability = pd.to_numeric(rows.get("model_probability"), errors="coerce")
    market_pass = rows.get("spy_trend_positive", False).fillna(False).astype(bool)
    scanner_pass = scanner_score > min_scanner_score

    output_rows = []
    for threshold in thresholds:
        model_pass = probability > threshold
        signal_mask = scanner_pass & model_pass & market_pass
        executable_mask = signal_mask & rows.get("execution_valid", False).fillna(False).astype(bool)
        labeled = rows.loc[signal_mask].dropna(subset=["label"])
        symbols = rows.loc[signal_mask, "symbol"] if "symbol" in rows.columns else pd.Series(dtype=object)
        output_rows.append(
            {
                "period": period,
                "threshold": threshold,
                "scanner_pass_days": int(scanner_pass.sum()),
                "model_pass_days": int(model_pass.sum()),
                "signal_days": int(signal_mask.sum()),
                "executable_signal_days": int(executable_mask.sum()),
                "symbols_with_signals": int(symbols.nunique()),
                "label_rows": int(len(labeled)),
                "label_success_rate": _safe_float(pd.to_numeric(labeled["label"], errors="coerce").mean()),
                "mean_probability_on_signals": _safe_float(probability.loc[signal_mask].mean()),
            }
        )
    return pd.DataFrame(output_rows)


def _safe_float(value: object) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return parsed
