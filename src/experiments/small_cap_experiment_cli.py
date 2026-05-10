from __future__ import annotations

import argparse
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd

from src.data.downloader import download_ticker
from src.data.small_cap_data_preparer import SmallCapPreparedData, prepare_small_cap_historical_data
from src.data.small_cap_metadata_builder import MetadataProvider, write_small_cap_metadata_csv, yfinance_metadata_provider
from src.experiments.small_cap_historical_runner import SmallCapHistoricalRunConfig, run_small_cap_historical_report

Downloader = Callable[[str, str, str | None], pd.DataFrame]


def run_small_cap_historical_experiment(
    metadata_path: str | Path,
    output_dir: str | Path,
    start: str,
    end: str | None = None,
    symbols: list[str] | None = None,
    iwm_symbol: str = "IWM",
    vix_symbol: str | None = "^VIX",
    downloader: Downloader = download_ticker,
    metadata_diagnostics: pd.DataFrame | None = None,
    run_config: SmallCapHistoricalRunConfig = SmallCapHistoricalRunConfig(),
) -> dict[str, Any]:
    static_metadata = _load_metadata(metadata_path)
    selected_metadata = _select_metadata(static_metadata, symbols)
    selected_symbols = selected_metadata["symbol"].astype(str).tolist()

    raw_frames = _download_symbol_frames(selected_symbols, start, end, downloader)
    iwm_frame = downloader(iwm_symbol, start, end)
    vix_frame = downloader(vix_symbol, start, end) if vix_symbol else None
    prepared_data = prepare_small_cap_historical_data(
        raw_frames,
        iwm_frame=iwm_frame,
        static_metadata=selected_metadata,
        vix_frame=vix_frame,
    )
    run_result = run_small_cap_historical_report(
        prepared_data.candidate_metadata,
        prepared_data.frames,
        output_dir=output_dir,
        iwm_frame=prepared_data.iwm_frame,
        start=run_config.start or start,
        end=run_config.end or end,
        metadata_diagnostics=metadata_diagnostics,
        config=run_config,
    )
    return {"prepared_data": prepared_data, "run_result": run_result}


def run_small_cap_watchlist_experiment(
    symbols: list[str],
    metadata_output_path: str | Path,
    output_dir: str | Path,
    start: str,
    end: str | None = None,
    metadata_diagnostics_path: str | Path | None = None,
    iwm_symbol: str = "IWM",
    vix_symbol: str | None = "^VIX",
    metadata_provider: MetadataProvider = yfinance_metadata_provider,
    downloader: Downloader = download_ticker,
    run_config: SmallCapHistoricalRunConfig = SmallCapHistoricalRunConfig(),
) -> dict[str, Any]:
    metadata_result = write_small_cap_metadata_csv(
        symbols,
        metadata_output_path,
        diagnostics_path=metadata_diagnostics_path,
        provider=metadata_provider,
    )
    experiment_result = run_small_cap_historical_experiment(
        metadata_path=metadata_result.metadata_path,
        output_dir=output_dir,
        start=start,
        end=end,
        iwm_symbol=iwm_symbol,
        vix_symbol=vix_symbol,
        downloader=downloader,
        metadata_diagnostics=pd.DataFrame(metadata_result.diagnostics),
        run_config=run_config,
    )
    return {"metadata_result": metadata_result, "experiment_result": experiment_result}


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    symbols = _parse_symbols(args.symbols)
    if args.metadata_path:
        run_small_cap_historical_experiment(
            metadata_path=args.metadata_path,
            output_dir=args.output_dir,
            start=args.start,
            end=args.end,
            symbols=symbols,
            iwm_symbol=args.iwm_symbol,
            vix_symbol=args.vix_symbol,
        )
    else:
        if not symbols:
            raise SystemExit("--symbols is required when --metadata-path is not provided")
        if not args.metadata_output_path:
            raise SystemExit("--metadata-output-path is required when --metadata-path is not provided")
        run_small_cap_watchlist_experiment(
            symbols=symbols,
            metadata_output_path=args.metadata_output_path,
            metadata_diagnostics_path=args.metadata_diagnostics_path,
            output_dir=args.output_dir,
            start=args.start,
            end=args.end,
            iwm_symbol=args.iwm_symbol,
            vix_symbol=args.vix_symbol,
        )
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a historical small-cap swing research experiment.")
    parser.add_argument("--metadata-path", default=None, help="CSV with symbol, market_cap and is_etf columns.")
    parser.add_argument("--metadata-output-path", default=None, help="Optional one-shot metadata CSV output path.")
    parser.add_argument("--metadata-diagnostics-path", default=None, help="Optional one-shot metadata diagnostics CSV output path.")
    parser.add_argument("--output-dir", required=True, help="Directory where experiment artifacts will be written.")
    parser.add_argument("--start", required=True, help="Download and experiment start date.")
    parser.add_argument("--end", default=None, help="Optional download and experiment end date.")
    parser.add_argument("--symbols", default=None, help="Optional comma-separated symbol subset.")
    parser.add_argument("--iwm-symbol", default="IWM", help="IWM/Russell 2000 proxy ticker.")
    parser.add_argument("--vix-symbol", default="^VIX", help="VIX ticker. Use an empty string to disable.")
    return parser


def _load_metadata(metadata_path: str | Path) -> pd.DataFrame:
    path = Path(metadata_path)
    if not path.exists():
        raise FileNotFoundError(f"metadata_path not found: {path}")
    metadata = pd.read_csv(path)
    if "symbol" in metadata.columns:
        metadata["symbol"] = metadata["symbol"].astype(str)
    return metadata


def _select_metadata(static_metadata: pd.DataFrame, symbols: list[str] | None) -> pd.DataFrame:
    if symbols is None:
        return static_metadata.copy()
    selected = static_metadata[static_metadata["symbol"].astype(str).isin(symbols)].copy()
    missing = sorted(set(symbols) - set(selected["symbol"].astype(str)))
    if missing:
        raise ValueError(f"symbols not found in metadata: {missing}")
    return selected


def _download_symbol_frames(
    symbols: list[str],
    start: str,
    end: str | None,
    downloader: Downloader,
) -> dict[str, pd.DataFrame]:
    return {symbol: downloader(symbol, start, end) for symbol in symbols}


def _parse_symbols(raw: str | None) -> list[str] | None:
    if raw is None:
        return None
    symbols = [symbol.strip() for symbol in raw.split(",") if symbol.strip()]
    return symbols or None


if __name__ == "__main__":
    raise SystemExit(main())
