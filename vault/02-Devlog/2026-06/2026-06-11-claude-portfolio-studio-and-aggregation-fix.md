---
tipo: devlog
progetto: adaptive-equity-trading-lab
data: 2026-06-11
agente: claude
ultimo-aggiornamento: 2026-06-11
tags: [dashboard, streamlit, portfolio-studio, regime, bug-fix]
---

# Portfolio Studio (sito nuovo) + fix aggregazione esplosa

## Bug critico risolto

Le card del Portfolio Lab mostravano valori tipo `-2.6e15%`: gli stream proxy
contengono "rendimenti" di periodo fino a +1850% (somme additive di piu' trade
per giorno), e comporli con `(1+r).cumprod()` e' matematicamente invalido.

Fix in `workbench_portfolio_engine`: `_aggregate_curve()` rileva la modalita'
onesta (`compounded` solo se ogni periodo e' un rendimento frazionario
plausibile, soglia `COMPOUNDING_MAX_ABS_RETURN=0.5`, altrimenti `additive`)
e ogni summary espone `aggregation_mode`. La UI formatta `%` solo in modalita'
compounded, `u` (unita' additive) altrimenti; `pct()` ha una guardia
"fuori scala". Stesso trattamento in `build_regime_switching_portfolio_diagnostic`.

Verifica sul catalogo reale (102 componenti): da `-2.6e15%` a `+225.43 u`
dichiarati additivi.

## Sito nuovo: dashboard/studio.py

`Portfolio Studio` sostituisce la vecchia app sulla porta 8502 (la vecchia
`dashboard/app.py` resta come consolle audit legacy). Flusso in 3 step:

1. **Strategy Arena** - leaderboard di tutto il catalogo (salvate + factory),
   filtri famiglia/fonte, curva per ogni strategia.
2. **Regimi** - matrice Strategia x Regime dal router + best basket per regime
   (ricerca governata sui soli componenti ammessi).
3. **Composer** - portfolio regime-switching: in ogni periodo usa il basket
   del regime attivo; confronto dynamic vs static con bande regime sul grafico.

Motore nuovo: `src/experiments/regime_portfolio_studio.py`
(`optimize_basket_for_regime`, `compose_regime_switching_portfolio`,
`run_regime_studio`) - tutto diagnostic-only, `promotion_allowed=False` ovunque.

## Verifiche

- `tests/test_regime_portfolio_studio.py`: 6 passed (incluso il guard
  anti-esplosione con stream estremi).
- Suite engine/dashboard esistente: 33 passed.
- AppTest sulle 4 pagine dello Studio: nessuna eccezione.
- Pipeline completa su catalogo ridotto: 6/6 regimi con basket, 15s.
- Smoke run pipeline (catalogo 20): dynamic +758.75 u vs static +594.34 u -
  numero proxy additive, NON evidenza promuovibile.

## Governance

Nessuna provider query, nessun download, nessun backtest vero, nessuna
promozione. Lo Studio mostra il disclaimer PROXY/DIAGNOSTICA in ogni pagina.

## Avvio

```powershell
.\.venv-lab\Scripts\streamlit.exe run dashboard/studio.py
```

Porta e tema dark da `.streamlit/config.toml`.

## Aggiornamento sera: TRIAL-STUDIO-OOS-001

Prima validazione out-of-sample dell'engine per-regime, con la gate DSR
dormiente finalmente collegata. Vedi
[[Report-Studio-OOS-Validation-2026-06-11]]. Verdetto:
`OOS_POSITIVE__BEATS_STATIC__OUTLIER_ROBUST__DSR_FAIL`.

## Replica TRIAL-STUDIO-OOS-002

Cutoff 2024-01-01: ex-top3 sign flip, robustezza NON replicata. Stessi 2-3
stream dominanti in entrambi i trial (artefatto di scala dell'aggregazione
additiva). Vedi [[Report-Studio-OOS-Replication-2026-06-11]]. Selezione
engine non validata; prossimo passo: normalizzazione a volatilita' unitaria
nel composer prima di nuovi trial.

## Trial 003/004: vol normalization replica

Con stream normalizzati a vol unitaria (fattori in-sample only) la robustezza
ex-top3 replica su entrambi i cutoff e i risultati diventano percentuali vere:
dynamic +51.2%/+70.2% vs static -22.9%/-38.0%, DD max -3.9%/-9.1%. DSR ancora
FAIL contro la barra deflazionata (60 trial). Vedi
[[Report-Studio-OOS-VolNorm-Replication-2026-06-11]]. Nessuna promozione.

## Trial 005-007: regola preregistrata, tutte le gate passate

Top-5 Sharpe in-sample per regime, zero ricerca, vol-norm: tutte e 4 le gate
passano su tre cutoff (DSR 0.99999+ a multiplicita' preregistrata). Caveat di
multiplicita' di programma documentato nel report. Protocollo ora CONGELATO:
prossima replica solo su dati nuovi, senza modifiche. Vedi
[[Report-Studio-OOS-Preregistered-Rule-2026-06-11]].

## Kronos per difesa: valutazione

Evidenza archiviata (CANDIDATE-006): come filtro alpha non batte i filtri
random same-count (percentile 0.622, serve ~0.95; winner capture <50%);
archiviato senza promozione. Eventuale ruolo difensivo (RISK_OVERLAY nel
router) richiede un trial preregistrato che batta il baseline semplice gia'
validato (index regime classifier, vol ordering OOS preservato) su riduzione
drawdown a parita' di esposizione, usando le feature Kronos archiviate senza
nuova inference. Spec proposta: TRIAL-KRONOS-DEFENSE-001.

## TRIAL-KRONOS-DEFENSE-001: duello perso

Inference bounded Kronos-mini su SPY (68 as-of, coverage 99.7%): riduce il
drawdown ma senza merito di timing (p19 vs shift casuali) e perde 3x in
efficienza dal regime classifier a parita' di esposizione. Kronos NON entra
nel router. Vedi [[Report-Kronos-Defense-Duel-2026-06-11]].

## Sessione estesa: consolidamento

- TRIAL-HOUSE-001: ricetta congelata + difesa classifier come oggetto unico -
  TUTTE le gate passate su entrambi i cutoff (+35.8%/-2.8% DD e +66.8%/-4.3% DD,
  costi inclusi). Vedi [[Report-House-Portfolio-Trial-2026-06-11]].
- Replica mensile del protocollo congelato schedulata (primo del mese, 9:00).
- Igiene vault: 0 note orfane (da 133), indici aggiornati (+58 devlog, +111
  report), creata [[Stato-Corrente]] e linkata in cima all'INDEX.
- Spec congelata del prossimo gate: [[TRIAL-TRUE-ETF-001-Spec]].
