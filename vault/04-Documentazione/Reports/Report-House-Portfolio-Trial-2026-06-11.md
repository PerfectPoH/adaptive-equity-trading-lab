---
tipo: report
progetto: adaptive-equity-trading-lab
data: 2026-06-11
trial: TRIAL-HOUSE-001
ultimo-aggiornamento: 2026-06-11
tags: [house-portfolio, regime, defense, oos, dsr]
---

# Report - House Portfolio Trial (TRIAL-HOUSE-001)

Decision: `HOUSE_PASS_ALL_GATES_BOTH_CUTOFFS`

## Oggetto

"Portfolio della casa" = ricetta per-regime congelata
([[Report-Studio-OOS-Preregistered-Rule-2026-06-11]]) x esposizione del
regime classifier (vincitore del duello difensivo,
[[Report-Kronos-Defense-Duel-2026-06-11]]), con 10 bps di costo per unita'
di esposizione scambiata. Prima volta che attacco e difesa vengono testati
come oggetto unico.

## Risultati OOS (percentuali compounded, stream vol-normalizzati)

| Metrica | Cutoff 2025 | Cutoff 2024 |
|---|---|---|
| House return | +35.8% | +66.8% |
| House max DD | **-2.8%** | **-4.3%** |
| Return/DD house | 12.9 | 15.6 |
| Return/DD non difeso | 6.7 | 12.3 |
| Static (riferimento) | -22.9% / -29.2% DD | -38.0% / -43.1% DD |
| Costi pagati | 0.45% | 0.90% |
| DSR (trial=2) | PASS (1.0) | PASS (1.0) |

Gates: H1 OOS positivo PASS; H2 risk-adjusted migliore del non difeso PASS;
H3 DSR PASS; H4 coerenza sui due cutoff PASS.

## Lettura

La difesa cede ~14-19 punti di rendimento ma piu' che dimezza il drawdown:
il rapporto rendimento/dolore quasi raddoppia sul cutoff 2025. La
combinazione e' il candidato canonico per il true backtest.

## Limiti

Sempre stream proxy vol-normalizzati con rebalancing giornaliero implicito;
costi modellati solo sul cambio di esposizione del classifier, non sul
turnover interno delle sleeve. NESSUNA promozione. Prossimo gate:
[[TRIAL-TRUE-ETF-001-Spec]] (true backtest su universo ammissibile).

## Artifact

`experiments/runs/house_trial_001_20260611_120842/`
