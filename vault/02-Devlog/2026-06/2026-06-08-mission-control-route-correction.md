# Mission Control Route Correction

Date: 2026-06-08

Status: MISSION_CONTROL_ROUTE_CORRECTION_COMPLETE

Issue:
- Regime Playbook, Data Vault, and Decision Ledger were routed through the same full Results/Data renderer.
- This made the pages look nearly identical except for the first explanatory row.

Correction:
- Regime Playbook now renders only market regime routing, operating notes, and regime audit details.
- Data Vault now renders only admissible-data readiness, delisted coverage, provider paths, and data-gate audit details.
- Decision Ledger now renders final decisions, provider-query rows, and raw decision audit details.
- A regression test now blocks these focused routes from delegating to the full data dashboard renderer.

Governance:
- No provider query was performed.
- No market-data download was performed.
- No backtest was performed.
- No promotion state changed.

Verification:
- Python compile checks passed.
- Dashboard Mission Control tests passed.
- Browser smoke checks confirmed the three routes have distinct page markers and no Streamlit traceback.


Vedi [[Devlog-Index]] e [[Stato-Corrente]].
