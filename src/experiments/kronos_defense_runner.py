"""Runner per TRIAL-KRONOS-DEFENSE-001.

Fase A (bounded inference, autorizzata dall'owner in chat il 2026-06-11):
  Kronos-mini CPU su SPY (snapshot locale, nessun download), as-of ogni 5
  giorni di borsa nel periodo OOS, context 250 bar, pred_len 5, 20 sample.
Fase B: duello difensivo vs index regime classifier sul path OOS del
  TRIAL-STUDIO-OOS-005.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.experiments.candidate_006_kronos_smoke import (  # noqa: E402
    prepare_kronos_input_frame,
    summarize_kronos_forecast,
)
from src.experiments.kronos_defense_trial import KronosDefenseConfig, run_kronos_defense_duel  # noqa: E402

SPY_SNAPSHOT = Path("data/snapshots/SPY_2026-05-09.csv")
REGIME_HISTORY = Path("experiments/runs/regime_index_001_20260610/regime_history.csv")
KRONOS_REPO_DIR = Path(".external/kronos")


def _load_spy() -> pd.DataFrame:
    frame = pd.read_csv(SPY_SNAPSHOT, parse_dates=["Date"]).set_index("Date")
    return frame[["Open", "High", "Low", "Close", "Volume"]]


def _build_predictor(sample_count: int):
    sys.path.insert(0, str(KRONOS_REPO_DIR.resolve()))
    from model import Kronos, KronosPredictor, KronosTokenizer  # type: ignore

    tokenizer = KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-2k")
    model = Kronos.from_pretrained("NeoQuasar/Kronos-mini")
    predictor = KronosPredictor(model, tokenizer, device="cpu", max_context=512)

    def predict(input_frame: pd.DataFrame, pred_len: int) -> pd.DataFrame:
        x_timestamp = pd.Series(input_frame.index)
        y_timestamp = pd.Series(pd.bdate_range(input_frame.index[-1] + pd.Timedelta(days=1), periods=pred_len))
        forecast = predictor.predict(
            df=input_frame,
            x_timestamp=x_timestamp,
            y_timestamp=y_timestamp,
            pred_len=pred_len,
            T=1.0,
            top_p=0.9,
            sample_count=sample_count,
            verbose=False,
        )
        forecast.index = pd.to_datetime(y_timestamp).dt.tz_localize(None)
        return forecast

    return predict


def run_inference(start: str, *, every: int, lookback: int, sample_count: int, out_path: Path) -> pd.DataFrame:
    spy = _load_spy()
    asof_dates = [d for d in spy.index[::1] if d >= pd.Timestamp(start)][::every]
    predict = _build_predictor(sample_count)
    rows: list[dict] = []
    for i, asof in enumerate(asof_dates):
        history = spy.loc[:asof]
        if len(history) < lookback:
            continue
        input_frame = prepare_kronos_input_frame(history, lookback_rows=lookback)
        forecast = predict(input_frame, 5)
        features = summarize_kronos_forecast(input_frame, forecast)
        rows.append({"symbol": "SPY", "as_of_date": asof.strftime("%Y-%m-%d"), **features})
        if (i + 1) % 10 == 0:
            print(f"  inference {i + 1}/{len(asof_dates)}", flush=True)
    frame = pd.DataFrame(rows)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out_path, index=False)
    return frame


def _oos_returns_from_trial(run_glob: str) -> pd.Series:
    candidates = sorted(Path("experiments/runs").glob(run_glob))
    if not candidates:
        raise FileNotFoundError(f"nessun run trovato per {run_glob}")
    curves = pd.read_csv(candidates[-1] / "oos_curves.csv")
    cumulative = pd.Series(curves["dynamic"].to_numpy(), index=pd.to_datetime(curves["period"]))
    return (1.0 + cumulative) / (1.0 + cumulative.shift(1).fillna(0.0)) - 1.0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2025-01-01")
    parser.add_argument("--every", type=int, default=5)
    parser.add_argument("--lookback", type=int, default=250)
    parser.add_argument("--sample-count", type=int, default=20)
    parser.add_argument("--skip-inference", action="store_true")
    parser.add_argument("--source-run", default="studio_oos_005_*")
    args = parser.parse_args()

    out_dir = Path("experiments/runs") / f"kronos_defense_001_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    out_dir.mkdir(parents=True, exist_ok=True)
    features_path = out_dir / "kronos_spy_features.csv"

    existing = sorted(Path("experiments/runs").glob("kronos_defense_001_*/kronos_spy_features.csv"))
    if args.skip_inference and existing:
        features = pd.read_csv(existing[-1])
        print(f"feature riusate da {existing[-1]}")
    else:
        print("FASE A: inference Kronos-mini su SPY (bounded, CPU)...", flush=True)
        features = run_inference(args.start, every=args.every, lookback=args.lookback, sample_count=args.sample_count, out_path=features_path)
    print(f"feature: {len(features)} as-of dates")

    returns = _oos_returns_from_trial(args.source_run)
    regime_history = pd.read_csv(REGIME_HISTORY)
    result = run_kronos_defense_duel(returns, features, regime_history, KronosDefenseConfig())
    (out_dir / "kronos_defense_result.json").write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print("ARTIFACTS:", out_dir)
    print("VERDICT:", result["verdict"])
    print(json.dumps({k: result[k] for k in ("coverage", "unthrottled", "kronos", "classifier", "random_timing", "gates")}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
