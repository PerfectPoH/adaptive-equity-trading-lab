# Candidate 017 EODHD Micro-Probe 003 Validation Correction

The run respected the pre-run gate and did not retain raw payloads, build a dataset, run a backtest, or promote a strategy.

During artifact review, the EOD OHLCV checks were found to be too permissive: HTTP 200 responses with one non-OHLCV row were summarized as `row_count: 1` and marked `PASS` even when `first_date`, `last_date`, and `has_adjusted_close` were missing.

Run 003 remains non-admissible because the delisted-list check was blocked, but its EOD PASS labels must not be used as evidence of EODHD OHLCV admissibility. The validation rule is reinforced so required EOD checks must include dated adjusted-close OHLCV rows.
