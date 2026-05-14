---
tipo: decision-record
progetto: adaptive-equity-trading-lab
data: 2026-05-14
tags: [decision, small-cap, ranking-exits, trial-accounting, governance]
---

# Report Small-Cap RankEx Strategic Decision - 2026-05-14

## Decisione

```text
CLOSE SIMPLE RANKING TRACK
DO NOT OPEN TRIAL-RANKEX-002 YET
DO NOT REUSE TRIAL-RANKEX-001
NO OOS 2025
NO PAPER TRADING
NO DISCRETIONARY SWEEP
```

Dopo la validation failure di `TRIAL-RANKEX-001`, il ranking semplice basato su `small_cap_scanner_score` viene chiuso come ipotesi non promuovibile.

## Razionale

`TRIAL-RANKEX-001` ha mostrato due fatti distinti:

1. l'infrastruttura di validazione funziona;
2. il ranking semplice non e' sufficientemente robusto.

La validation ha prodotto un ritorno nominale positivo e superiore ai benchmark principali, ma ha fallito il gate pre-registrato di robustezza ex-top3:

```text
portfolio_return: 5.62%
ticker_holding_window: 2.54%
random_entry_baseline: 1.94%
pnl_excluding_top_1: 1189.50
pnl_excluding_top_3: -6282.54
sign_flip_excluding_top_3: true
insufficient_funds: 0
```

Questo significa che la meccanica portfolio e' sana, ma il risultato non e' robusto. La performance dipende da pochi outlier e non puo' essere promossa verso OOS o paper trading.

## Interpretazione tecnica

### Cosa ha funzionato

- Il sizing risk-based ha rimosso il vecchio problema di cash starvation.
- La validation ha avuto `insufficient_funds=0` su 100 trade.
- Il manifest con `trial_accounting` ha preservato tracciabilita' e separazione dal `config_hash`.
- I gate pre-registrati hanno impedito una promozione basata su equity curve nominalmente positiva.

### Cosa non ha funzionato

- `small_cap_scanner_score` non ordina i candidati in modo abbastanza predittivo.
- I tie-breaker `relative_volume_20d` e `open_to_close_return` non salvano l'ipotesi base.
- Il sistema batte random/ticker in modo nominale, ma non sopravvive alla rimozione dei primi tre trade.
- La mediana trade resta negativa, quindi la distribuzione e' dominata da coda destra invece che da edge diffuso.

## Decisione sul bivio

Tra:

```text
A. chiudere il track ranking semplice e cambiare ipotesi
B. pre-registrare subito TRIAL-RANKEX-002 con feature ranking alternative
```

la scelta e':

```text
A - chiudere il track ranking semplice
```

Motivo: aprire immediatamente `TRIAL-RANKEX-002` su feature vicine allo stesso setup rischierebbe di diventare un salvataggio retroattivo della famiglia `RankEx`. La cosa corretta e' congelare prima la conclusione: il ranking semplice sullo scanner esistente non e' promotable.

## Prossima direzione consigliata

La prossima ricerca non deve essere una variazione del ranking semplice. Deve essere una nuova materia prima, con nuovo trial ID e nuova pre-registrazione.

Direzione preferita:

```text
Cross-Sectional Momentum vs IWM
```

Motivo:

- e' piu' coerente con l'evidenza che le small-cap hanno code destre forti;
- cerca di selezionare forza relativa persistente, non solo il miglior candidato tra segnali deboli;
- consente benchmark naturali contro IWM, equal-weight universe, random entry e ticker holding window;
- puo' essere definita come ipotesi nuova, non come tuning di `TRIAL-RANKEX-001`.

Direzione alternativa da tenere in backlog, ma non preferita ora:

```text
Mean Reversion / Panic Reversal Estremo
```

Motivo: puo' essere interessante, ma e' piu' esposta a knife-catching, gap risk e dipendenza da execution quality. Va affrontata solo con stop/exit design molto rigorosi e non come prossimo passo immediato.

## Vincoli per il prossimo trial

Un eventuale nuovo trial deve:

- usare nuovo `trial_id`, non `TRIAL-RANKEX-001`;
- avere pre-registrazione autonoma prima di qualunque run;
- dichiarare design/validation/OOS windows;
- dichiarare baseline e gate ex-topN prima dei risultati;
- non modificare retroattivamente soglie del vecchio setup;
- non usare OOS 2025 finche' la validation non passa;
- non attivare paper trading prima di validation e OOS.

## Stato finale

```text
TRIAL-RANKEX-001: CLOSED / FAILED VALIDATION / NOT PROMOTED
SIMPLE SCANNER-SCORE RANKING: CLOSED
NEXT ALLOWED WORK: draft a preregistered Cross-Sectional Momentum research spec, no run
```

Vedi [[Report-Small-Cap-RankEx-Trial-001-Validation-2026-05-14]], [[small-cap-ranking-exits-research-track]], [[Roadmap-Master]], [[backlog]], [[Project-Handoff]].
