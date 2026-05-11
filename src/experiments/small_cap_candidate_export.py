from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.backtest.small_cap_execution import SmallCapExecutionConfig, add_small_cap_execution_columns
from src.data.small_cap_data_quality import SmallCapDataQualityConfig, build_small_cap_data_quality_report
from src.data.universe_builder import SmallCapUniverseConfig, build_small_cap_universe
from src.risk.market_regime_guardrail import MarketRegimeGuardrailConfig, add_market_regime_guardrail_columns
from src.scanner.small_cap_swing_scanner import SmallCapSwingScannerConfig, add_small_cap_swing_scanner_columns


@dataclass(frozen=True)
class SmallCapCandidateExportConfig:
    universe: SmallCapUniverseConfig = SmallCapUniverseConfig()
    data_quality: SmallCapDataQualityConfig = SmallCapDataQualityConfig(min_bars=1)
    scanner: SmallCapSwingScannerConfig = SmallCapSwingScannerConfig()
    regime: MarketRegimeGuardrailConfig = MarketRegimeGuardrailConfig()
    execution: SmallCapExecutionConfig = SmallCapExecutionConfig()
    equity: float = 100_000


EXPORT_COLUMNS = [
    "as_of",
    "symbol",
    "operational_candidate",
    "passes_universe_filter",
    "universe_rejection_reasons",
    "data_quality_status",
    "data_quality_warnings",
    "data_quality_errors",
    "small_cap_setup",
    "small_cap_scanner_score",
    "small_cap_scanner_pass",
    "small_cap_scanner_reject_reason",
    "gap_pct",
    "open_to_close_return",
    "close_position_daily_range",
    "intraday_range_pct",
    "relative_volume_20d",
    "atr_pct",
    "distance_from_20d_high",
    "rolling_volatility_20d",
    "market_regime_trade_allowed",
    "market_regime_block_reason",
    "small_cap_execution_valid",
    "small_cap_execution_skip_reason",
    "small_cap_entry_reference_price",
    "small_cap_entry_price",
    "small_cap_position_size",
    "small_cap_position_notional",
    "small_cap_max_liquidity_notional",
    "avg_dollar_volume_20d",
]


def build_small_cap_candidate_export(
    candidate_metadata: pd.DataFrame,
    frames: dict[str, pd.DataFrame],
    as_of: str | pd.Timestamp | None = None,
    config: SmallCapCandidateExportConfig = SmallCapCandidateExportConfig(),
    operational_only: bool = True,
) -> pd.DataFrame:
    metadata = candidate_metadata.copy()
    symbols = metadata["symbol"].astype(str).tolist() if "symbol" in metadata.columns else []
    universe = build_small_cap_universe(metadata, config=config.universe, passed_only=False)
    quality = build_small_cap_data_quality_report(symbols, frames, config=config.data_quality)
    quality_by_symbol = quality.set_index("symbol").to_dict("index") if not quality.empty else {}

    rows = []
    for _, universe_row in universe.iterrows():
        symbol = str(universe_row["symbol"])
        rows.append(_build_symbol_export_row(symbol, universe_row, quality_by_symbol.get(symbol, {}), frames.get(symbol), as_of, config))

    export = pd.DataFrame(rows)
    if export.empty:
        return pd.DataFrame(columns=EXPORT_COLUMNS)

    for column in EXPORT_COLUMNS:
        if column not in export.columns:
            export[column] = pd.NA
    export = export[EXPORT_COLUMNS]
    if operational_only:
        export = export[export["operational_candidate"].fillna(False).astype(bool)].copy()
    for column in (
        "operational_candidate",
        "passes_universe_filter",
        "small_cap_scanner_pass",
        "market_regime_trade_allowed",
        "small_cap_execution_valid",
    ):
        if column in export.columns:
            export[column] = export[column].fillna(False).astype(bool).astype(object)
    return export.reset_index(drop=True)


def write_small_cap_candidate_export(export: pd.DataFrame, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    export.to_csv(output_path, index=False)
    return output_path


def _build_symbol_export_row(
    symbol: str,
    universe_row: pd.Series,
    quality_row: dict[str, object],
    frame: pd.DataFrame | None,
    as_of: str | pd.Timestamp | None,
    config: SmallCapCandidateExportConfig,
) -> dict[str, object]:
    base = _base_row(symbol, universe_row, quality_row, as_of)
    if frame is None or frame.empty:
        base["operational_candidate"] = False
        return base

    prepared = _prepare_symbol_frame(symbol, frame, universe_row, as_of)
    if prepared.empty:
        base["operational_candidate"] = False
        base["data_quality_status"] = "fail"
        base["data_quality_errors"] = _append_reason(str(base.get("data_quality_errors", "") or ""), "no_bars_on_or_before_as_of")
        return base

    candidate_index = _candidate_index(prepared, as_of)
    scanned = add_small_cap_swing_scanner_columns(prepared, config=config.scanner)
    scanned["signal"] = scanned["small_cap_scanner_pass"].fillna(False).astype(bool)
    guarded = add_market_regime_guardrail_columns(scanned, config=config.regime)
    executed = add_small_cap_execution_columns(guarded, equity=config.equity, config=config.execution)
    latest = executed.loc[candidate_index]

    base.update({column: latest.get(column, base.get(column, pd.NA)) for column in EXPORT_COLUMNS})
    base["as_of"] = pd.to_datetime(latest.name).date().isoformat()
    base["symbol"] = symbol
    base["passes_universe_filter"] = bool(universe_row.get("passes_universe_filter", False))
    base["universe_rejection_reasons"] = str(universe_row.get("rejection_reasons", "") or "")
    base["data_quality_status"] = str(quality_row.get("status", "fail") or "fail")
    base["data_quality_warnings"] = str(quality_row.get("warnings", "") or "")
    base["data_quality_errors"] = str(quality_row.get("errors", "") or "")
    base["operational_candidate"] = bool(
        base["passes_universe_filter"]
        and base["data_quality_status"] in {"pass", "warn"}
        and bool(latest.get("small_cap_scanner_pass", False))
        and bool(latest.get("market_regime_trade_allowed", False))
        and bool(latest.get("small_cap_execution_valid", False))
    )
    return base


def _base_row(
    symbol: str,
    universe_row: pd.Series,
    quality_row: dict[str, object],
    as_of: str | pd.Timestamp | None,
) -> dict[str, object]:
    return {
        "as_of": _as_of_label(as_of),
        "symbol": symbol,
        "operational_candidate": False,
        "passes_universe_filter": bool(universe_row.get("passes_universe_filter", False)),
        "universe_rejection_reasons": str(universe_row.get("rejection_reasons", "") or ""),
        "data_quality_status": str(quality_row.get("status", "fail") or "fail"),
        "data_quality_warnings": str(quality_row.get("warnings", "") or ""),
        "data_quality_errors": str(quality_row.get("errors", "missing_data") or ""),
    }


def _prepare_symbol_frame(
    symbol: str,
    frame: pd.DataFrame,
    universe_row: pd.Series,
    as_of: str | pd.Timestamp | None,
) -> pd.DataFrame:
    data = frame.copy().sort_index()
    if as_of is not None:
        as_of_timestamp = pd.Timestamp(as_of)
        after_as_of = data.index[data.index > as_of_timestamp]
        if len(after_as_of):
            data = data[data.index <= after_as_of[0]]
        else:
            data = data[data.index <= as_of_timestamp]
    data["symbol"] = symbol
    for column in ("market_cap", "price", "avg_volume_20d", "avg_dollar_volume_20d", "is_etf"):
        if column in universe_row.index and column not in data.columns:
            data[column] = universe_row[column]
    return data


def _candidate_index(data: pd.DataFrame, as_of: str | pd.Timestamp | None) -> object:
    if as_of is None:
        return data.index[-1]
    eligible = data.index[data.index <= pd.Timestamp(as_of)]
    if len(eligible) == 0:
        return data.index[-1]
    return eligible[-1]


def _as_of_label(as_of: str | pd.Timestamp | None) -> str:
    if as_of is None:
        return ""
    return pd.Timestamp(as_of).date().isoformat()


def _append_reason(existing: str, reason: str) -> str:
    return reason if not existing else f"{existing};{reason}"
