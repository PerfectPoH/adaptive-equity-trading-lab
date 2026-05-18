# Report - Approved mini-panel provider sensitivity diagnostic - 2026-05-18

## Status

```text
APPROVED_MINI_PANEL_DIAGNOSTIC_COMPLETED
PANEL_ID: MINIPANEL-PREREG-PA-SMALLCAP-001-001
PREREGISTRATION_ID: PREREG-PA-SMALLCAP-001
BATCH_TRIAL_ID: MINIPANEL-TRIAL-001
GIT_SHA: 586f579
NEW_PROVIDER_QUERY_COUNT: 3
NO_RAW_PAYLOAD_RETENTION
NO_BACKTEST
NO_SWEEP
NO_STRATEGY_PROMOTION
NO_PAPER_LIVE
```

## Execution outputs

```text
experiments/provider_aware_research/execution_outputs/MINIPANEL-PREREG-PA-SMALLCAP-001-001/
```

Produced files:

```text
mini_panel_execution_manifest.json
mini_panel_diagnostic_summary.json
provider_sensitivity_mini_panel_results.csv
mini_panel_interpretation_report.md
```

## Candidate results

```text
IOVA 2025-07:
  databento_status: pass
  databento_rows: 7
  polygon_status: OK
  return_delta: 0.045024828927805516
  sensitivity_class: minor_price_or_return_delta

CABA 2022-08:
  databento_status: error:BentoClientError
  databento_rows: 0
  polygon_status: OK
  return_delta: null
  sensitivity_class: provider_unavailable

IOVA 2025-12:
  databento_status: pass
  databento_rows: 7
  polygon_status: OK
  return_delta: 0.013289905083675918
  sensitivity_class: minor_price_or_return_delta
```

## Safety verification

```text
raw_payload_retained: false
raw_response_path: RAW_RESPONSE_RETENTION_NOT_ENABLED for all rows
raw files found: 0
secret/API-key strings found in output directory: 0
backtest_performed: false
strategy_promotion: false
```

## Interpretation

The mini-panel provides limited provider-sensitivity evidence for three approved new candidate checks only. Two IOVA cases returned minor price or return deltas; CABA had provider unavailability from Databento while Polygon reference lookup was OK. These results do not authorize strategy promotion, paper trading, live trading, sweeps, or any broader conclusion beyond this bounded diagnostic panel.
