---
tipo: feature-spec
stato: closed-simple-ranking-not-promoted
progetto: adaptive-equity-trading-lab
data: 2026-05-13
tags: [feature, research-track, small-cap, ranking, exits, trial-accounting]
---

# Small-Cap Ranking/Exits Research Track

## Stato

```text
SIMPLE RANKING CLOSED / NOT PROMOTED
```

Questo documento registra il track separato di ricerca su ranking intra-candidate, gestione uscite e portfolio construction per small-cap long-only. Dopo `TRIAL-RANKEX-001`, il sotto-track ranking semplice basato su `small_cap_scanner_score` e' chiuso come non promuovibile.

Non e' una continuazione promozionale del setup archiviato:

```text
breakout_continuation
open_to_close_return >= 0.10
IWM close > EMA200
holding_period_bars = 5
risk_fraction = 0.01
```

Quel setup resta:

```text
ARCHIVED / NOT PROMOTED
```

## Perche' aprire un track separato

Il fix risk-based sizing ha chiarito che:

```text
il tooling portfolio e' utile
il vecchio +169% era leverage/path artifact
il segnale lordo contiene alcune regioni interessanti
il portfolio corretto non batte benchmark e fallisce ex-top3
```

Quindi il problema residuo non va trattato aggiungendo un filtro in-sample al setup archiviato. Va trattato, se vale la pena, come nuova ipotesi:

```text
il valore lordo esiste ma viene perso da ranking, exits o construction
```

## Non-obiettivi

- Nessun paper trading.
- Nessun ranking production.
- Nessun nuovo filtro per salvare retroattivamente la track archiviata.
- Nessun riuso del vecchio +169% come prova di edge.
- Nessuna ottimizzazione libera di soglie senza trial accounting.
- Nessun cambio di `risk_fraction=0.01` come leva per migliorare il risultato.

## Domande di ricerca

### RQ-001 - Ranking intra-candidate

Quando piu' candidati competono nello stesso giorno, esiste un ranking che batte:

```text
ticker_holding_window
random_entry_baseline
equal_weight_universe
current scanner score
```

senza diventare proxy di overfitting?

### RQ-002 - Exit management

La holding period fissa a 5 barre perde valore rispetto a uscite alternative pre-registrate?

Famiglie consentite solo dopo definizione TDD/manifest:

```text
time-based variants
ATR/volatility stop management
profit-taking rules
trailing stop rules
regime deterioration exit
```

### RQ-003 - Portfolio construction

La strategia perde valore per concentrazione, correlazione o collisione tra candidati?

Aree candidate:

```text
max symbols per day
cluster/correlation exposure
sector/theme cap
notional smoothing
candidate queue policy
```

## Trial accounting iniziale

Ogni esperimento deve registrare almeno:

| Campo | Obbligatorio |
|---|---|
| `trial_id` | si |
| `research_question` | si |
| `hypothesis_family` | si |
| `train_or_design_window` | si |
| `validation_window` | si |
| `oos_window` | si |
| `universe_definition` | si |
| `baseline_run_id` | si |
| `candidate_run_id` | si |
| `benchmark_set` | si |
| `ex_top_n_results` | si |
| `decision` | si |
| `notes_on_multiple_testing` | si |

## Trial ledger iniziale

| Trial | Scope | Stato | Note |
|---|---|---|---|
| TRIAL-INFRA-001 | risk-based sizing fix | chiuso/promosso | trial infrastrutturale, non edge trial |
| TRIAL-ARCHIVE-001 | breakout/open_to_close/EMA200 corrected validation | chiuso/non promosso | setup archiviato |
| TRIAL-RANKEX-001 | ranking intra-candidate by existing scanner score | closed/failed validation/not promoted | vedi [[Report-Small-Cap-RankEx-Trial-001-Validation-2026-05-14]] e [[Report-Small-Cap-RankEx-Strategic-Decision-2026-05-14]]; no OOS/no promotion |

## Baseline obbligatorie

Ogni esperimento del track deve confrontarsi contro:

```text
cash_flat
IWM proxy
equal_weight_universe
random_entry_baseline
ticker_holding_window
archived setup with corrected risk sizing
```

Il confronto contro l'archived setup serve solo come riferimento tecnico, non come prova promozionale.

## Gate di promozione

Una variante puo' avanzare solo se supera tutti questi gate:

1. batte `ticker_holding_window` e `random_entry_baseline` nel periodo di validazione;
2. non cambia segno dopo rimozione top 1 e top 3 trade;
3. mostra miglioramento non concentrato in un solo anno/regime;
4. mantiene `insufficient_funds` vicino a zero senza aumentare `risk_fraction`;
5. produce manifest riproducibile e config hash;
6. passa OOS/universe robustness pre-registrata;
7. ha trial accounting aggiornato.

## Primo passo consentito

Prima di qualunque backtest o sweep:

```text
non eseguire OOS 2025 per `TRIAL-RANKEX-001`; eventuali nuove ipotesi richiedono nuovo trial ID e nuova pre-registrazione
```

La validation di `TRIAL-RANKEX-001` e' fallita sul gate ex-top3; il ranking semplice e' chiuso. Non eseguire OOS, paper trading o sweep discrezionali su questo trial. La direzione preferita resta cross-sectional momentum vs IWM, ma prima serve un gate documentale data-quality/methodology: yfinance audit, universe as-of, random bootstrap, multiple-testing ledger e backtester audit.

## Stato operativo

```text
Sotto-track ranking semplice chiuso.
TRIAL-RANKEX-001 fallito in validation.
Nessuna strategia promossa.
Data Quality Audit completato: `yfinance` daily alone non e' utilizzabile come fonte primaria per nuovi trial small-cap. Lessons Learned completato: lavoro small-cap 2026-05-09..2026-05-14 riclassificato come stress test metodologico/infrastrutturale. Scaffolding check per negative control fixed large-cap/ETF completato con `TECHNICAL_PASS`; `TRIAL-NCTRL-001` pre-registrato come property-based negative control ma non eseguibile finche' P5/P6/P4/reporting/accounting non sono implementati con TDD.
```

Vedi [[2026-05-13-cascade-small-cap-setup-archive-decision]], [[small-cap-swing-research-spec]], [[Roadmap-Master]], [[backlog]].
