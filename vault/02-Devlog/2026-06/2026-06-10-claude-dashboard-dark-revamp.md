---
tipo: devlog
progetto: adaptive-equity-trading-lab
data: 2026-06-10
agente: claude
ultimo-aggiornamento: 2026-06-10
tags: [dashboard, streamlit, ui, dark-theme, portfolio-lab]
---

# Dashboard Dark Revamp - Mission Control

## Contesto

La dashboard su porta 8502 era visivamente disorganizzata (tema chiaro custom sopra
widget Streamlit di default), il Portfolio Lab mostrava numeri incoerenti
(headline = somma additiva, curva = compounded) e diverse classi CSS del
router matrix non esistevano. Vedi [[Roadmap-Master]] e
[[2026-06-10-methodology-hardening-three-points]].

## Cosa e' cambiato

- `.streamlit/config.toml` nuovo: tema base dark nativo + porta 8502 di default.
- `dashboard/app.py`: design system dark mission-control completo (token CSS,
  card, pill, nav rail, alert, expander); tutti i 13 chart Plotly portati a
  `plotly_dark` con palette coerente; corrette le classi CSS mancanti del
  router matrix (`proxy/reduce/observe/overlay/block`) e gli alias `--lab-*`
  mai definiti.
- Coerenza numeri Portfolio Lab: il motore (`workbench_portfolio_engine`)
  espone `total_net_return_compounded` e `validation_net_return_compounded`
  accanto alle somme additive; la UI mostra percentuali compounded coerenti
  con la curva equity (helper `pct`/`pct_tone`, colori pos/neg).
- Copy misto IT/EN su Mission Brief, Portfolio Lab e nav rail.
- Test stantio `test_dashboard_main_uses_internal_rail_not_streamlit_sidebar`
  aggiornato al design "rail sempre visibile".

## Verifiche

- `py_compile` su tutti i file toccati: pass.
- `test_dashboard_app_bootstrap` + `test_mission_control_ui`: 12 passed.
- `test_workbench_portfolio_engine*`, `test_pctrl*`, `test_index_regime*`: 45 passed.
- Boot headless porta 8502: HTTP 200, nessun traceback.
- Check sintetico: headline compounded == ultimo punto equity curve.

## Governance

Nessuna provider query, nessun download dati, nessun backtest, nessuna promozione.

## Prossima mossa

Spaccare `app.py` (4.100+ righe) in moduli per pagina; valutare alleggerimento
del render Portfolio Lab (la governed search gira a ogni rerun della pagina).
