# Devlog - Approved mini-panel provider sensitivity diagnostic - 2026-05-18

Executed the approved bounded provider sensitivity mini-panel after preflight passed 17/17 on commit `586f579`.

```text
panel_id: MINIPANEL-PREREG-PA-SMALLCAP-001-001
new_provider_query_count: 3
candidate_count_with_anchor: 4
provider_query_performed: true
raw_payload_retained: false
backtest_performed: false
strategy_promotion: false
```

Results:

```text
IOVA 2025-07: minor_price_or_return_delta, return_delta 0.045024828927805516
CABA 2022-08: provider_unavailable, Databento BentoClientError, Polygon OK
IOVA 2025-12: minor_price_or_return_delta, return_delta 0.013289905083675918
```

No raw payload files were retained and no strategy action was promoted.


Vedi [[Devlog-Index]] e [[Stato-Corrente]].
