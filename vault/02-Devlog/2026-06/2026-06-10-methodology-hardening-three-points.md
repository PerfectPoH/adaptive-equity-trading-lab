---
progetto: adaptive-equity-trading-lab
data: 2026-06-10
autore: cascade
status: COMPLETE
scope: methodology_hardening
related:
  - TRIAL-PCTRL-001
  - REGIME-INDEX-001
  - PORTFOLIO-LAB-FIX-001
  - TRIAL-NCTRL-001
---

# Methodology hardening - tre punti a costo zero

## Sintesi

Eseguiti i punti 1, 3 e 4 del piano d'azione: positive control + power curve della
DSR gate, return matrix del Portfolio Lab riscritta NaN-aware, regime classifier
basato su feature di indice con validazione OOS. Tutti e tre i lavori sono
self-contained, non richiedono dati premium, e hanno test di copertura.

## 1. TRIAL-PCTRL-001 - Positive Control & DSR Power Curve

Controparte del NCTRL: il negative control verifica che la pipeline rigetti il
rumore; questo verifica che la pipeline **accetti** un edge noto e misura il
sample size minimo necessario.

**File aggiunti**

- `src/experiments/pctrl_synthetic_edge_simulator.py` - simulator con
  `PositiveControlConfig`, `PowerCurveSpec`, `evaluate_positive_control_cell`,
  `run_power_curve`, `minimum_sample_size_for_power`.
- `experiments/configs/pctrl_synthetic_edge_001.py` - runner che produce JSON,
  CSV e report Markdown.
- `tests/test_pctrl_synthetic_edge_simulator.py` - 6 test (pass/power
  monotonia, type-I bound, configurazione invalida, ecc.).

**Run artifacts**

- `experiments/runs/pctrl_synthetic_edge_001_20260610/power_curve_report.{json,md,csv}`

**Risultati principali** (sigma=0.02 per-trade, trial_count_searched=30, 300
bootstrap iterations per cella):

| effect mu | annual Sharpe | min N per 50% power | min N per 80% power |
| --- | ---: | ---: | ---: |
| 0.0000 (noise) | 0.00 | not reached | not reached |
| 0.0050 | 3.97 | 252 | 400 |
| 0.0075 | 5.95 | 150 | 200 |
| 0.0100 | 7.94 | 75 | 100 |

**Conclusione operativa.** XMOM e GapRev hanno prodotto 11-43 trade. A quei
sample size la DSR gate non puo' detectare un edge inferiore a Sharpe ~6
annualizzato. Qualunque "pass" storico a quel sample size e' dominato dalla
fortuna. La gate e' anche conservativa al ribasso (Type-I < 5% a tutte le N
testate per mu=0).

## 3. PORTFOLIO-LAB-FIX-001 - Return matrix riscritta NaN-aware

Tre bug strutturali in `build_component_return_matrix` e i suoi consumatori
risolti:

1. **Missing periods**: `pd.DataFrame(series_by_component).fillna(0.0)` ->
   `pd.DataFrame(series_by_component)`. I periodi mancanti restano NaN. Tutti
   gli aggregatori downstream usano `.sum(skipna=True)`, `.mean(skipna=True)`
   o nuovi helper NaN-aware.
2. **Curva cumulativa**: `returns.cumsum()` -> `_compound_cumulative_returns`
   `(1+r).cumprod() - 1`. Adesso la cifra finale e' un rendimento di
   portafoglio, non una somma di stream.
3. **Pool dei componenti**: nuovo parametro `require_real_dates=True` esclude
   componenti il cui indice e' fatto solo di placeholder `step-XXXXX`, che
   non hanno allineamento temporale con il resto del portafoglio.

**Helpers nuovi** (in `src/experiments/workbench_portfolio_engine.py`):

- `_has_real_date_index(series)` - True se almeno un indice parsifica come
  data.
- `_compound_cumulative_returns(returns)` - `(1+r).cumprod()-1` con NaN come
  cash.
- `_active_period_mean(matrix)` - media per riga sui componenti vivi
  nel periodo.

**Consumatori aggiornati**

- `run_portfolio_diagnostic` - weighting NaN-aware e curva compounded.
- `_run_portfolio_search_candidate` - idem.
- `_inverse_volatility_weights` - std calcolata sui periodi vivi, non
  zero-padded.
- `dashboard/lab_dashboard_data.py::build_regime_switching_portfolio_diagnostic`
  - static baseline = media sui componenti vivi nel periodo, dynamic sleeve
  rinormalizzato sui componenti effettivamente presenti, totale dynamic/static
  compounded.

**Test nuovi** in `tests/test_workbench_portfolio_engine_nan_aware.py` (8
test). Aggiornato un assert esistente in `test_workbench_portfolio_engine.py`
che assumeva il vecchio fill 0.0.

## 4. REGIME-INDEX-001 - Regime classifier index-feature con validazione OOS

Rifondata la regime map sulle feature di un indice (SPY) invece che su
string-matching del nome di strategia. Classifier deterministico, parametrico,
no fitting in-sample.

**File aggiunti**

- `src/risk/index_regime_classifier.py` - `IndexRegimeConfig`,
  `compute_index_regime_features`, `classify_index_regime_raw`,
  `apply_hysteresis`, `classify_index_regime`,
  `validate_regime_predictiveness`.
- `experiments/configs/index_regime_classifier_001.py` - runner che applica
  il classifier a `data/snapshots/SPY_2026-05-09.csv` (2018-01-02 -> 2026-05-08,
  2099 bar) e genera la validazione OOS.
- `tests/test_index_regime_classifier.py` - 7 test (feature panel,
  isteresi, ANOVA su dati sintetici, ecc.).

**Run artifacts**

- `experiments/runs/regime_index_001_20260610/regime_history.csv`
- `experiments/runs/regime_index_001_20260610/regime_train_stats.csv`
- `experiments/runs/regime_index_001_20260610/regime_test_stats.csv`
- `experiments/runs/regime_index_001_20260610/regime_validation_report.{json,md}`

**Regimi**: TREND_UP, TREND_DOWN, HIGH_VOL, QUIET_RANGE, MIXED_NORMAL.
Hysteresis 5 bar (cambio label richiede 5 raw bar consecutivi).

**Risultato OOS** (split chronologico 60/40, forward horizon 20d):

| Metrica | Train F | Train p~ | Test F | Test p~ |
| --- | ---: | ---: | ---: | ---: |
| Forward return | 8.33 | 0.0000 | 28.83 | 0.0000 |
| Forward vol    | 72.48 | 0.0000 | 66.17 | 0.0000 |

| Stability | Rank corr train -> test |
| --- | ---: |
| Forward vol ordering | +0.50 (preserved) |
| Forward return ordering | -0.50 (flipped) |

**Conclusione onesta.** Il regime e' uno **strumento di gestione del rischio**
(ordering della vol preservato OOS), NON un alpha direzionale (l'ordering del
rendimento si inverte OOS). Usarlo come segnale long/short equivale a fitting
in-sample.

## Dashboard pulito

Aggiunta una nuova landing page minimale in `dashboard/research_review.py`
(~420 righe, no Streamlit-extras, CSS leggero) che mostra in un solo colpo lo
stato dei tre artefatti del giorno. Si lancia con:

```bash
streamlit run dashboard/research_review.py
```

Il `dashboard/app.py` da 4635 righe non e' stato toccato.

## Test recap

```bash
python3 -m pytest \
  tests/test_workbench_portfolio_engine.py \
  tests/test_pctrl_synthetic_edge_simulator.py \
  tests/test_workbench_portfolio_engine_nan_aware.py \
  tests/test_index_regime_classifier.py \
  tests/test_statistical_gate_harness.py
```

Risultato: **38 passed, 2 warnings (cosmetic pandas warning, no functional
impact)**.

## Cosa non e' fatto (rimosso dal piano per evitare scope creep)

- Punto 2: collegare DSR + N_eff al runner dei trial come campo obbligatorio
  del preregistration validator. Richiede un passo strutturale sul ledger
  globale dei trial; pianificato come lavoro successivo.
- Punto 5: decisione dati (Norgate/Sharadar vs pivot ETF). Decisione di
  business, fuori dallo scope di questa sessione.
- Punto 6: consolidamento di `src/experiments` (80+ validator ad-hoc) in un
  motore generico di preregistrazione. Refactor non banale, da pianificare.

## File summary

```text
SRC (modified):
  src/experiments/workbench_portfolio_engine.py
  dashboard/lab_dashboard_data.py

SRC (new):
  src/experiments/pctrl_synthetic_edge_simulator.py
  src/risk/index_regime_classifier.py
  dashboard/research_review.py

CONFIGS (new):
  experiments/configs/pctrl_synthetic_edge_001.py
  experiments/configs/index_regime_classifier_001.py

TESTS (new):
  tests/test_pctrl_synthetic_edge_simulator.py
  tests/test_workbench_portfolio_engine_nan_aware.py
  tests/test_index_regime_classifier.py

TESTS (modified):
  tests/test_workbench_portfolio_engine.py

RUN ARTIFACTS:
  experiments/runs/pctrl_synthetic_edge_001_20260610/
  experiments/runs/regime_index_001_20260610/

VAULT (new):
  vault/02-Devlog/2026-06/2026-06-10-methodology-hardening-three-points.md
```


Vedi [[Devlog-Index]] e [[Stato-Corrente]].
