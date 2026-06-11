"""REGIME-INDEX-001 — Index-feature regime classifier with OOS validation.

Replaces the in-sample, string-matched regime map of the Workbench
Portfolio Lab with a deterministic classifier on SPY price/vol features.
Produces an OOS validation report so the regime claim is testable rather
than asserted.

Run::

    python -m experiments.configs.index_regime_classifier_001
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from src.risk.index_regime_classifier import (
    IndexRegimeConfig,
    classify_index_regime,
    validate_regime_predictiveness,
)


TRIAL_ID = "REGIME-INDEX-001"
RUN_ID = "run_regime_index_001_20260610"
OUTPUT_DIR = Path("experiments/runs/regime_index_001_20260610")
SPY_PATH = Path("data/snapshots/SPY_2026-05-09.csv")
TRAIN_FRACTION = 0.6
FORWARD_HORIZON = 20
CONFIG = IndexRegimeConfig()


def run_index_regime_trial() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if not SPY_PATH.exists():
        raise FileNotFoundError(f"SPY history not available at {SPY_PATH}")
    prices = pd.read_csv(SPY_PATH, parse_dates=["Date"], index_col="Date").sort_index()
    classified = classify_index_regime(prices, config=CONFIG)

    label_distribution = classified["regime"].dropna().value_counts().to_dict()
    regime_history = (
        classified[["close", "trend_strength", "vol_percentile", "range_distance", "regime_raw", "regime"]]
        .dropna(subset=["regime"])
        .copy()
    )
    regime_history.index.name = "date"
    regime_history.to_csv(OUTPUT_DIR / "regime_history.csv", float_format="%.8f")

    validation = validate_regime_predictiveness(
        classified,
        forward_horizon=FORWARD_HORIZON,
        train_fraction=TRAIN_FRACTION,
    )
    validation.train_per_regime.to_csv(OUTPUT_DIR / "regime_train_stats.csv", float_format="%.8f")
    validation.test_per_regime.to_csv(OUTPUT_DIR / "regime_test_stats.csv", float_format="%.8f")

    payload: dict[str, Any] = {
        "trial_id": TRIAL_ID,
        "run_id": RUN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_file": str(SPY_PATH),
        "config": {
            "long_trend_window": CONFIG.long_trend_window,
            "short_trend_window": CONFIG.short_trend_window,
            "volatility_window": CONFIG.volatility_window,
            "high_vol_percentile": CONFIG.high_vol_percentile,
            "low_vol_percentile": CONFIG.low_vol_percentile,
            "range_band": CONFIG.range_band,
            "hysteresis_bars": CONFIG.hysteresis_bars,
            "percentile_window": CONFIG.percentile_window,
            "forward_horizon": FORWARD_HORIZON,
            "train_fraction": TRAIN_FRACTION,
        },
        "data_range": {
            "start": str(prices.index.min().date()),
            "end": str(prices.index.max().date()),
            "n_obs": int(len(prices)),
        },
        "label_distribution_all_history": label_distribution,
        "validation": {
            "train_size": validation.train_split_idx,
            "test_size": validation.test_split_idx,
            "forward_horizon": validation.forward_horizon,
            "train_f_return": validation.train_f_return,
            "train_p_return": validation.train_p_return,
            "test_f_return": validation.test_f_return,
            "test_p_return": validation.test_p_return,
            "train_f_vol": validation.train_f_vol,
            "train_p_vol": validation.train_p_vol,
            "test_f_vol": validation.test_f_vol,
            "test_p_vol": validation.test_p_vol,
            "rank_correlation_return_train_test": validation.rank_correlation_return,
            "rank_correlation_vol_train_test": validation.rank_correlation_vol,
        },
    }

    (OUTPUT_DIR / "regime_validation_report.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "regime_validation_report.md").write_text(_render_markdown(payload, validation), encoding="utf-8")
    return payload


def _render_markdown(payload: dict[str, Any], validation: Any) -> str:
    cfg = payload["config"]
    data = payload["data_range"]
    val = payload["validation"]
    rank_vol = val["rank_correlation_vol_train_test"]
    rank_ret = val["rank_correlation_return_train_test"]
    lines: list[str] = []
    lines.append(f"# {payload['trial_id']} - Index-Feature Regime Classifier (OOS Validation)")
    lines.append("")
    lines.append(f"Run ID: `{payload['run_id']}`")
    lines.append(f"Generated: `{payload['generated_at_utc']}`")
    lines.append(f"Source: `{payload['source_file']}`")
    lines.append(f"History: `{data['start']}` to `{data['end']}` ({data['n_obs']} bars)")
    lines.append("")
    lines.append("## Configuration")
    lines.append("")
    lines.append("| Parameter | Value |")
    lines.append("| --- | --- |")
    for k, v in cfg.items():
        lines.append(f"| `{k}` | `{v}` |")
    lines.append("")
    lines.append("## Label distribution (all history, post-hysteresis)")
    lines.append("")
    lines.append("| Regime | Bars |")
    lines.append("| --- | --- |")
    for regime, count in sorted(payload["label_distribution_all_history"].items()):
        lines.append(f"| `{regime}` | {count} |")
    lines.append("")
    lines.append("## OOS validation result")
    lines.append("")
    lines.append("Methodology: classify on the full history, then chronologically split")
    lines.append(f"at {int(cfg['train_fraction']*100)}% (train) / "
                 f"{int((1-cfg['train_fraction'])*100)}% (test). For each session, compute")
    lines.append(f"the forward {cfg['forward_horizon']}-day log return and realised vol.")
    lines.append("If the regime captures something real, the per-regime statistics should")
    lines.append("(a) differ within each split (significant ANOVA F) and (b) preserve their")
    lines.append("ordering across splits (positive rank correlation).")
    lines.append("")
    lines.append("| Metric | Train F | Train p~ | Test F | Test p~ |")
    lines.append("| --- | ---: | ---: | ---: | ---: |")
    lines.append(
        f"| Forward return | {val['train_f_return']:.2f} | {val['train_p_return']:.4f} | "
        f"{val['test_f_return']:.2f} | {val['test_p_return']:.4f} |"
    )
    lines.append(
        f"| Forward vol | {val['train_f_vol']:.2f} | {val['train_p_vol']:.4f} | "
        f"{val['test_f_vol']:.2f} | {val['test_p_vol']:.4f} |"
    )
    lines.append("")
    lines.append("| Stability check | Rank corr (train→test) |")
    lines.append("| --- | ---: |")
    lines.append(f"| Mean forward return ordering | {rank_ret:.2f} |")
    lines.append(f"| Mean forward vol ordering | {rank_vol:.2f} |")
    lines.append("")
    lines.append("## Honest interpretation")
    lines.append("")
    lines.append(_honest_interpretation(val))
    lines.append("")
    lines.append("## Per-regime statistics (train)")
    lines.append("")
    lines.append(validation.train_per_regime.round(6).to_markdown())
    lines.append("")
    lines.append("## Per-regime statistics (test)")
    lines.append("")
    lines.append(validation.test_per_regime.round(6).to_markdown())
    lines.append("")
    return "\n".join(lines) + "\n"


def _honest_interpretation(val: dict[str, Any]) -> str:
    vol_signal = val["test_f_vol"] > 2.0 and val["rank_correlation_vol_train_test"] > 0.0
    return_signal = val["test_f_return"] > 2.0 and val["rank_correlation_return_train_test"] > 0.0
    lines: list[str] = []
    if vol_signal:
        lines.append(
            "- Forward-volatility separation by regime is significant OOS and the ordering "
            "is preserved. The regime label is a usable **risk filter**."
        )
    else:
        lines.append(
            "- Forward-volatility separation by regime is weak or unstable OOS. The regime "
            "should not be used as a risk filter without further work."
        )
    if return_signal:
        lines.append(
            "- Forward-return separation by regime is significant OOS and the ordering is "
            "preserved. The regime carries a directional signal."
        )
    else:
        lines.append(
            "- Forward-return separation by regime is unstable OOS (rank correlation "
            f"{val['rank_correlation_return_train_test']:.2f}). The regime should NOT be "
            "used as a directional alpha; using it that way would be in-sample fitting."
        )
    return "\n".join(lines)


def main() -> int:
    payload = run_index_regime_trial()
    print(json.dumps(
        {"trial_id": payload["trial_id"], "run_id": payload["run_id"], "output_dir": str(OUTPUT_DIR)},
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
