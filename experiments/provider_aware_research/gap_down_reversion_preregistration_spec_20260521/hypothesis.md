# Hypothesis

Status: `SPEC_ONLY_NOT_EXECUTED`

Preregistration id: `PREREG-GAPREV-001`

Trial id: `TRIAL-GAPREV-001`

## Primary Hypothesis

US equities that open with an extreme overnight gap-down, show abnormal opening-session volume, and reclaim intraday VWAP before a fixed late-morning cutoff will exhibit positive post-cost intraday mean-reversion over a fixed holding window.

## Null Hypothesis

After realistic spread, slippage and market-impact costs, VWAP-reclaim gap-down candidates do not outperform a preregistered intraday benchmark and do not survive DSR-based multiple-testing correction.

## Why This Is Separate From XMOM

XMOM-001 studied cross-sectional momentum over multi-day holding windows.

`TRIAL-GAPREV-001` studies intraday reversion after overnight dislocation. It must not reuse XMOM-001 thresholds, trade outcomes, or catalyst-specific winners.

## Required Future Data

- intraday OHLCV at minimum;
- preferably trades/quotes for spread and VWAP realism;
- timestamped regular-session calendar;
- provider coverage contract;
- no raw-provider payload retention unless separately licensed and approved.

## Non-Goals

- No prediction of FDA/biotech binary outcomes.
- No earnings timestamp probe.
- No discretionary chart pattern trading.
- No parameter sweep over gap thresholds or reclaim times.
