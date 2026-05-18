# DPE data-quality audit layer summary

```text
DPE_DATA_QUALITY_AUDIT_LAYER_CREATED
SOURCE: derived provider artifacts only
NO_NEW_PROVIDER_QUERY
NO_RAW_RETENTION
NO_BACKTEST
NO_OOS
NO_SWEEP
NO_LIVE_OR_PAPER_TRADING
```

The layer converts existing Databento and Polygon provider-evaluation evidence into data-quality audit inputs. Every DPE event remains `caveat`; this is expected because adjusted factors, full PIT universe, full security master, halt feed, offering metadata and raw storage rights are still unavailable or blocked.

Allowed next use: provider join feasibility and data-quality audit interpretation only.

## Interpretation update

```text
DATA_QUALITY_AUDIT_INTERPRETATION_EXECUTED
USABLE_FOR_DATA_QUALITY_AUDIT_WITH_CAVEATS
NOT_USABLE_FOR_STRATEGY_PERFORMANCE_CLAIMS
TRIALS_REMAIN_BLOCKED
```

Downstream warning policy added: `downstream_warning_policy.csv`.
