from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

MetadataProvider = Callable[[str], dict[str, object]]
METADATA_COLUMNS = ["symbol", "market_cap", "is_etf"]
DIAGNOSTIC_COLUMNS = ["symbol", "status", "reason"]


@dataclass(frozen=True)
class SmallCapMetadataBuildResult:
    metadata: pd.DataFrame
    diagnostics: list[dict[str, str]]


@dataclass(frozen=True)
class SmallCapMetadataWriteResult:
    metadata: pd.DataFrame
    diagnostics: list[dict[str, str]]
    metadata_path: Path
    diagnostics_path: Path | None


def build_small_cap_metadata(symbols: list[str], provider: MetadataProvider) -> SmallCapMetadataBuildResult:
    rows: list[dict[str, object]] = []
    diagnostics: list[dict[str, str]] = []
    for symbol in _normalize_symbols(symbols):
        try:
            provided = provider(symbol)
        except Exception as exc:  # noqa: BLE001 - metadata collection should continue across symbols.
            diagnostics.append(_diagnostic(symbol, f"provider_failed:{exc}"))
            continue
        reason = _invalid_reason(provided)
        if reason:
            diagnostics.append(_diagnostic(symbol, reason))
            continue
        rows.append(
            {
                "symbol": symbol,
                "market_cap": int(provided["market_cap"]),
                "is_etf": bool(provided["is_etf"]),
            }
        )
    metadata = pd.DataFrame(rows, columns=METADATA_COLUMNS)
    return SmallCapMetadataBuildResult(metadata=metadata, diagnostics=diagnostics)


def write_small_cap_metadata_csv(
    symbols: list[str],
    output_path: str | Path,
    diagnostics_path: str | Path | None = None,
    provider: MetadataProvider | None = None,
) -> SmallCapMetadataWriteResult:
    if provider is None:
        provider = yfinance_metadata_provider
    result = build_small_cap_metadata(symbols, provider=provider)
    metadata_path = Path(output_path)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    result.metadata.to_csv(metadata_path, index=False)
    written_diagnostics_path = Path(diagnostics_path) if diagnostics_path is not None else None
    if written_diagnostics_path is not None:
        written_diagnostics_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(result.diagnostics, columns=DIAGNOSTIC_COLUMNS).to_csv(written_diagnostics_path, index=False)
    return SmallCapMetadataWriteResult(
        metadata=result.metadata,
        diagnostics=result.diagnostics,
        metadata_path=metadata_path,
        diagnostics_path=written_diagnostics_path,
    )


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    write_small_cap_metadata_csv(
        _parse_symbols(args.symbols),
        args.output_path,
        diagnostics_path=args.diagnostics_path,
    )
    return 0


def yfinance_metadata_provider(symbol: str) -> dict[str, object]:
    import yfinance as yf

    ticker = yf.Ticker(symbol)
    info = getattr(ticker, "fast_info", None)
    market_cap = _market_cap_from_fast_info(info)
    if market_cap is None:
        market_cap = ticker.info.get("marketCap")
    quote_type = str(ticker.info.get("quoteType", "")).upper()
    return {"market_cap": market_cap, "is_etf": quote_type == "ETF"}


def _normalize_symbols(symbols: list[str]) -> list[str]:
    normalized = [str(symbol).strip().upper() for symbol in symbols if str(symbol).strip()]
    return sorted(dict.fromkeys(normalized))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build small-cap metadata CSV from a ticker watchlist.")
    parser.add_argument("--symbols", required=True, help="Comma-separated ticker list.")
    parser.add_argument("--output-path", required=True, help="Metadata CSV output path.")
    parser.add_argument("--diagnostics-path", default=None, help="Optional diagnostics CSV output path.")
    return parser


def _parse_symbols(raw: str) -> list[str]:
    return [symbol.strip() for symbol in raw.split(",") if symbol.strip()]


def _invalid_reason(provided: dict[str, object]) -> str:
    if "market_cap" not in provided or pd.isna(provided["market_cap"]):
        return "missing_market_cap"
    if "is_etf" not in provided or pd.isna(provided["is_etf"]):
        return "missing_is_etf"
    try:
        market_cap = int(provided["market_cap"])
    except (TypeError, ValueError):
        return "invalid_market_cap"
    if market_cap <= 0:
        return "invalid_market_cap"
    return ""


def _diagnostic(symbol: str, reason: str) -> dict[str, str]:
    return {"symbol": symbol, "status": "fail", "reason": reason}


def _market_cap_from_fast_info(info: Any) -> object:
    if info is None:
        return None
    if isinstance(info, dict):
        return info.get("market_cap") or info.get("marketCap")
    return getattr(info, "market_cap", None) or getattr(info, "marketCap", None)


if __name__ == "__main__":
    raise SystemExit(main())
