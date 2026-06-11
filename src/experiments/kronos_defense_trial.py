"""TRIAL-KRONOS-DEFENSE-001: Kronos come overlay difensivo vs regime classifier.

Domanda preregistrata: a parita' di esposizione media, l'overlay difensivo
guidato da Kronos (feature di forecast su SPY) riduce il drawdown del path
OOS congelato PIU' del baseline semplice (index regime classifier)?

Regole fissate PRIMA di leggere i risultati (zero sweep):
  - Kronos:      exposure 0.25 se prob_up <= 0.40 oppure drawdown_proxy <= -0.05,
                 altrimenti 1.0; vale dal giorno successivo all'as-of fino al
                 forecast successivo.
  - Classifier:  exposure 0.25 in HIGH_VOL, 0.50 in TREND_DOWN, altrimenti 1.0.
  - Confronto a parita' di esposizione media (si scala il piu' esposto).
  - Baseline random: 500 shift circolari dell'esposizione Kronos; decisivo
    solo se il drawdown reale e' <= del 5o percentile degli shift.

Gates: G1 copertura >=80%; G2 il drawdown si riduce vs unthrottled;
G3 batte i shift circolari (p05); G4 efficienza difensiva > classifier.
Diagnostico-only: nessuna promozione.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class KronosDefenseConfig:
    prob_up_floor: float = 0.40
    drawdown_proxy_floor: float = -0.05
    kronos_defense_exposure: float = 0.25
    classifier_high_vol_exposure: float = 0.25
    classifier_trend_down_exposure: float = 0.50
    min_coverage: float = 0.80
    random_shifts: int = 500
    decisive_percentile: float = 0.05


def _compound(returns: pd.Series) -> tuple[float, float]:
    curve = (1.0 + returns.fillna(0.0)).cumprod()
    drawdown = curve / curve.cummax() - 1.0
    return float(curve.iloc[-1] - 1.0), float(drawdown.min())


def kronos_exposure_series(
    periods: pd.DatetimeIndex,
    features: pd.DataFrame,
    cfg: KronosDefenseConfig,
) -> tuple[pd.Series, float]:
    """Esposizione Kronos per ogni periodo + frazione di copertura."""

    frame = features.copy()
    frame["as_of_date"] = pd.to_datetime(frame["as_of_date"], errors="coerce")
    frame = frame.dropna(subset=["as_of_date"]).sort_values("as_of_date")
    exposures: list[float] = []
    covered = 0
    for period in periods:
        valid = frame[frame["as_of_date"] < period]
        if valid.empty:
            exposures.append(1.0)
            continue
        row = valid.iloc[-1]
        # un forecast vale al massimo 10 giorni di borsa
        if (period - row["as_of_date"]).days > 14:
            exposures.append(1.0)
            continue
        covered += 1
        defensive = (
            float(row["kronos_probability_up"]) <= cfg.prob_up_floor
            or float(row["kronos_forecast_drawdown_proxy"]) <= cfg.drawdown_proxy_floor
        )
        exposures.append(cfg.kronos_defense_exposure if defensive else 1.0)
    return pd.Series(exposures, index=periods, dtype=float), covered / max(len(periods), 1)


def classifier_exposure_series(
    periods: pd.DatetimeIndex,
    regime_history: pd.DataFrame,
    cfg: KronosDefenseConfig,
) -> pd.Series:
    frame = regime_history.copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame = frame.dropna(subset=["date"]).sort_values("date")
    mapping = {"HIGH_VOL": cfg.classifier_high_vol_exposure, "TREND_DOWN": cfg.classifier_trend_down_exposure}
    exposures: list[float] = []
    for period in periods:
        valid = frame[frame["date"] < period]
        regime = str(valid.iloc[-1]["regime"]) if not valid.empty else "UNKNOWN"
        exposures.append(mapping.get(regime, 1.0))
    return pd.Series(exposures, index=periods, dtype=float)


def _overlay_metrics(returns: pd.Series, exposure: pd.Series) -> dict[str, float]:
    total, max_dd = _compound(returns * exposure)
    return {"total_return": round(total, 6), "max_drawdown": round(max_dd, 6), "mean_exposure": round(float(exposure.mean()), 6)}


def run_kronos_defense_duel(
    returns: pd.Series,
    kronos_features: pd.DataFrame,
    regime_history: pd.DataFrame,
    config: KronosDefenseConfig | None = None,
) -> dict[str, Any]:
    cfg = config or KronosDefenseConfig()
    periods = pd.DatetimeIndex(pd.to_datetime(returns.index, errors="coerce"))
    returns = pd.Series(returns.to_numpy(), index=periods, dtype=float)

    kronos_exp, coverage = kronos_exposure_series(periods, kronos_features, cfg)
    classifier_exp = classifier_exposure_series(periods, regime_history, cfg)

    # parita' di esposizione media: scala il piu' esposto verso il piu' difensivo
    target = min(kronos_exp.mean(), classifier_exp.mean())
    kronos_eq = kronos_exp * (target / kronos_exp.mean()) if kronos_exp.mean() > 0 else kronos_exp
    classifier_eq = classifier_exp * (target / classifier_exp.mean()) if classifier_exp.mean() > 0 else classifier_exp

    unthrottled = _overlay_metrics(returns, pd.Series(1.0, index=periods))
    kronos_m = _overlay_metrics(returns, kronos_eq)
    classifier_m = _overlay_metrics(returns, classifier_eq)

    def efficiency(metrics: dict[str, float]) -> float:
        dd_gain = metrics["max_drawdown"] - unthrottled["max_drawdown"]  # >0 = meno drawdown
        ret_cost = unthrottled["total_return"] - metrics["total_return"]  # >0 = rendimento ceduto
        return round(dd_gain / max(ret_cost, 1e-9), 6)

    # baseline: shift circolari dell'esposizione Kronos (stessa distribuzione, timing casuale)
    rng = np.random.default_rng(20260611)
    values = kronos_eq.to_numpy()
    shift_dds: list[float] = []
    for _ in range(cfg.random_shifts):
        offset = int(rng.integers(1, len(values) - 1))
        _, dd = _compound(returns * pd.Series(np.roll(values, offset), index=periods))
        shift_dds.append(dd)
    shift_dds_arr = np.asarray(shift_dds)
    percentile = float((shift_dds_arr >= kronos_m["max_drawdown"]).mean())  # quota di shift con DD peggiore o uguale
    decisive = kronos_m["max_drawdown"] >= float(np.quantile(shift_dds_arr, 1.0 - cfg.decisive_percentile))

    gates = {
        "G1_coverage": coverage >= cfg.min_coverage,
        "G2_reduces_drawdown": kronos_m["max_drawdown"] > unthrottled["max_drawdown"],
        "G3_beats_random_timing": bool(decisive),
        "G4_beats_classifier_efficiency": efficiency(kronos_m) > efficiency(classifier_m),
    }
    verdict = "KRONOS_DEFENSE_" + ("PASS" if all(gates.values()) else "FAIL") + "__" + "_".join(
        name.split("_")[0] for name, ok in gates.items() if not ok
    ).strip("_")
    return {
        "status": "KRONOS_DEFENSE_DUEL_COMPLETE",
        "trial_id": "TRIAL-KRONOS-DEFENSE-001",
        "coverage": round(coverage, 4),
        "unthrottled": unthrottled,
        "kronos": {**kronos_m, "efficiency": efficiency(kronos_m)},
        "classifier": {**classifier_m, "efficiency": efficiency(classifier_m)},
        "random_timing": {
            "shifts": cfg.random_shifts,
            "dd_better_than_share_of_shifts": round(percentile, 4),
            "decisive_at": cfg.decisive_percentile,
        },
        "gates": gates,
        "verdict": verdict,
        "promotion_allowed": False,
        "provider_query_performed": False,
        "interpretation": (
            "Duello difensivo su path OOS congelato e stream proxy: misura la capacita' "
            "di Kronos di togliere esposizione nei momenti giusti, non un alpha."
        ),
    }
