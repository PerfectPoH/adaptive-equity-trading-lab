---
tipo: decision-record
progetto: adaptive-equity-trading-lab
data: 2026-05-14
tags: [decision, small-cap, data-quality, multiple-testing, backtester-audit, governance]
---

# Report Small-Cap Data Quality Gate Decision - 2026-05-14

## Decisione

```text
DATA QUALITY AND METHODOLOGY GATE BEFORE NEXT SMALL-CAP TRIAL
NO TRIAL-XMOM-001 PREREGISTRATION YET
NO BACKTEST / NO VALIDATION / NO OOS / NO SWEEP
```

Prima di pre-registrare qualunque nuovo trial small-cap, incluso un eventuale cross-sectional momentum vs IWM, il progetto deve trattare data quality, multiple testing e backtester realism come gate primari.

## Razionale

La sequenza recente ha dimostrato disciplina sperimentale:

- il vecchio +169% e' stato declassato dopo il fix del risk-based sizing;
- `TRIAL-RANKEX-001` e' stato fermato nonostante ritorno nominale positivo;
- il ranking semplice e' stato chiuso senza aprire subito un trial di salvataggio.

Il rischio ora non e' piu' solo overfitting strategico. Il rischio maggiore e' misurare su una base dati o un simulatore non abbastanza affidabile per small-cap.

## Nuovi colli di bottiglia primari

### 1. Data quality small-cap

`yfinance` e l'universo retro-ricostruito possono distorcere in modo grave:

- delisting;
- reverse split;
- corporate actions;
- halt intraday;
- offerte/dilution;
- survivorship bias;
- universo definito oggi e applicato retroattivamente.

Per small-cap momentum, un universo `as-of` e' parte del segnale. Usare un file costruito oggi su date passate puo' rendere il trial informativamente vuoto anche se supera i gate.

### 2. Random baseline come distribuzione

Un singolo `random_entry_baseline` seedato non basta. La baseline random e' una variabile aleatoria e deve essere trattata come distribuzione:

```text
N random baselines
percentili 5/50/95
probabilita' che la strategia batta random
```

Un trial futuro deve confrontare la strategia contro la distribuzione random, non solo contro un punto.

### 3. Multiple testing ledger

Gli esperimenti small-cap gia' tentati hanno consumato gradi di liberta'. Prima di nuovi trial serve un ledger esplicito:

- famiglia ipotesi;
- trial count;
- sweep/ablation count;
- trial falliti/promossi;
- correzione ingenua iniziale tipo Bonferroni-style o soglia piu' severa.

Il Deflated Sharpe Ratio resta una milestone istituzionale, ma un contatore trial-family serve subito.

### 4. Backtester audit

Il bug su `risk_fraction` ha dimostrato che il planner puo' cambiare radicalmente l'interpretazione dei risultati. Prima di nuove conclusioni serve audit mirato del `SmallCapPortfolioBacktester` su:

- quando il cash viene liberato dopo exit;
- slippage entry/exit;
- commissioni e costi;
- prezzo di chiusura dei trade aperti a fine periodo;
- coerenza calendario/holidays;
- handling di gap e no-trade conditions.

### 5. News/event blindness

Sulle small-cap molti segnali sono news-driven. Per ora non serve integrare un motore news completo, ma la prossima specifica deve dichiarare il limite e definire almeno proxy o esclusioni future per:

- earnings vicini;
- offering/dilution;
- FDA/regulatory events;
- halt/suspension events.

### 6. Stop rule di categoria

Serve un budget esplicito per la categoria small-cap. Dopo il fallimento del setup archiviato e di `TRIAL-RANKEX-001`, la domanda non e' solo quale trial fare dopo, ma quanti tentativi small-cap con dati free sono ancora informativi.

## Gate prerequisito proposto

Prima di qualunque nuovo trial small-cap:

1. creare un data-quality audit plan per `yfinance` su small-cap;
2. selezionare 5-10 ticker/eventi noti, includendo almeno delisting/reverse split/halt/corporate action;
3. confrontare OHLCV disponibile contro fonti evento indipendenti;
4. documentare se le distorsioni invalidano trial small-cap daily-level;
5. aggiungere bootstrap random baseline come requisito metodologico;
6. creare ledger multiple-testing per le famiglie gia' tentate;
7. eseguire mini-audit documentale/TDD del backtester prima di ulteriori interpretazioni.

## Impatto sulla roadmap

La prossima voce non e' piu':

```text
redigere subito TRIAL-XMOM-001
```

ma:

```text
redigere Data Quality + Methodology Gate per small-cap
```

Solo dopo il gate si potra' decidere se pre-registrare `TRIAL-XMOM-001`.

## Stato operativo

```text
TRIAL-RANKEX-001: CLOSED
SIMPLE RANKING: CLOSED
NEXT SMALL-CAP TRIAL: BLOCKED BY DATA QUALITY GATE
NEXT ALLOWED WORK: data-quality audit spec / random baseline bootstrap spec / multiple-testing ledger / backtester audit plan
```

Vedi [[Report-Small-Cap-RankEx-Strategic-Decision-2026-05-14]], [[small-cap-ranking-exits-research-track]], [[small-cap-swing-research-spec]], [[Roadmap-Master]], [[backlog]], [[Project-Handoff]].
## Update 2026-05-14 - Data Quality Audit Spec preregistered

The first sub-gate is now specified in [[Report-Small-Cap-Data-Quality-Audit-Spec-2026-05-14]]. Status: `SPEC PRE-REGISTERED / NOT EXECUTED / NO TRIAL UNLOCKED`. Next allowed work is compiling an independent event list and executing only the data-quality audit. `TRIAL-XMOM-001` remains not authorized.
