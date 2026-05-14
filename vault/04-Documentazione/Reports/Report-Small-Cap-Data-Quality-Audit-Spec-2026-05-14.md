---
tipo: audit-spec
progetto: adaptive-equity-trading-lab
data: 2026-05-14
tags: [spec, small-cap, data-quality, yfinance, survivorship, governance]
---

# Report Small-Cap Data Quality Audit Spec - 2026-05-14

## Stato

```text
SPEC PRE-REGISTERED / NOT EXECUTED / NO TRIAL UNLOCKED
```

Questa spec definisce il primo sotto-gate del [[Report-Small-Cap-Data-Quality-Gate-Decision-2026-05-14]]. Non autorizza backtest, validation, OOS, sweep o pre-registrazione di `TRIAL-XMOM-001`.

## Obiettivo

Verificare empiricamente se `yfinance` e l'attuale pipeline daily OHLCV sono sufficientemente affidabili per trial small-cap daily-level.

La domanda e':

```text
I dati daily yfinance rappresentano in modo abbastanza fedele eventi small-cap critici da rendere informativo un futuro trial small-cap?
```

## Non-obiettivi

- Non selezionare una strategia.
- Non valutare performance.
- Non scegliere ticker da `yfinance`.
- Non usare risultati dell'audit per modificare retroattivamente trial chiusi.
- Non aprire `TRIAL-XMOM-001`.
- Non sostituire un provider istituzionale point-in-time.

## Principio di selezione campione

I ticker/eventi da auditare devono essere scelti da fonti indipendenti da `yfinance`.

Fonti ammesse:

- SEC EDGAR;
- FINRA;
- Nasdaq Trader / exchange notices;
- comunicati societari ufficiali;
- provider corporate-action/event indipendenti;
- liste pubbliche di halt, delisting o reverse split con data evento verificabile.

Fonte non ammessa per selezionare il campione:

```text
yfinance
```

`yfinance` puo' essere usato solo come oggetto da verificare.

## Dimensione campione

Campione minimo:

```text
5 eventi
```

Campione desiderato:

```text
8-10 eventi
```

Copertura minima obbligatoria:

| Categoria evento | Minimo |
|---|---:|
| Delisting / suspension / bankruptcy-like outcome | 1 |
| Reverse split | 1 |
| Trading halt / volatility halt / regulatory halt | 1 |
| Corporate action price-impacting | 1 |
| Offering / dilution / ATM-like event | 1 |

Se una categoria non e' reperibile con fonte indipendente affidabile in una sessione ragionevole, l'audit deve dichiarare la lacuna e non sostituirla con un evento scelto da performance yfinance.

## Criteri di inclusione evento

Ogni evento deve avere:

- ticker;
- data evento ufficiale;
- fonte indipendente;
- categoria evento;
- finestra di verifica;
- motivo per cui l'evento e' rilevante per small-cap backtesting.

Finestra standard:

```text
T-10 trading days .. T+10 trading days
```

Finestra estesa facoltativa:

```text
T-60 trading days .. T+60 trading days
```

La finestra estesa serve solo per reverse split, delisting e corporate action con effetti persistenti.

## Proprieta' da verificare

Per ogni evento, verificare `yfinance` su queste proprieta'.

### 1. Disponibilita' storico

- il ticker e' scaricabile;
- la finestra T-10..T+10 e' presente;
- non ci sono buchi non spiegati;
- il periodo dopo delisting/suspension non viene rappresentato come normale trading liquido.

### 2. Integrita' OHLCV

- open/high/low/close coerenti;
- volume non zero quando la fonte indipendente indica trading attivo;
- assenza di barre sintetiche sospette;
- assenza di return impossibili non spiegati da corporate action.

### 3. Corporate action adjustment

- reverse split riflesso correttamente;
- adjusted close coerente con close/raw ove applicabile;
- pre/post split non generano falsi breakout o falsi gap;
- eventuale split ratio documentato.

### 4. Halt e suspension awareness

- l'evento di halt/suspension e' riconoscibile o almeno non viene rappresentato come normale sessione tradabile;
- la pipeline daily non produce segnali su barre non realisticamente tradabili;
- eventuale gap post-halt e' visibile e non smussato.

### 5. Survivorship / availability bias

- il ticker resta interrogabile anche se delistato;
- se non resta interrogabile, l'assenza viene registrata come failure, non come dato mancante neutrale;
- la pipeline non puo' costruire universe storici usando solo ticker sopravvissuti.

### 6. Pipeline compatibility

Verificare se i dati scaricati potrebbero attraversare la pipeline attuale senza warning:

- universe builder;
- data-quality report;
- scanner/candidate export;
- backtester.

Questa verifica e' documentale o dry-inspection. Non autorizza run strategici.

## Metriche qualitative obbligatorie

Per ogni evento assegnare:

| Campo | Valori ammessi |
|---|---|
| `source_independent` | yes/no |
| `yfinance_downloadable` | yes/no |
| `event_window_complete` | yes/no/partial |
| `corporate_action_adjustment_ok` | yes/no/not_applicable/unclear |
| `halt_or_suspension_visible` | yes/no/not_applicable/unclear |
| `tradability_representation_ok` | yes/no/unclear |
| `pipeline_warning_required` | yes/no |
| `severity` | low/medium/high/critical |
| `verdict` | pass/caveat/fail |

## Soglie pre-registrate

### Verdict `usable`

```text
critical failures = 0
high severity failures <= 1
>= 80% eventi con verdict pass o caveat
nessuna categoria obbligatoria completamente non verificabile
halt/suspension non rappresentati come trading normale nei casi verificabili
```

Con `usable`, e' consentito procedere al secondo documento del gate metodologico, non direttamente a `TRIAL-XMOM-001`.

### Verdict `usable_with_caveats`

```text
critical failures = 0
high severity failures <= 2
>= 60% eventi con verdict pass o caveat
almeno una categoria obbligatoria ha caveat materiale
serve warning esplicito in ogni futura pre-registrazione small-cap
```

Con `usable_with_caveats`, e' consentito proseguire solo se la futura spec dichiara esplicitamente i caveat e aggiunge mitigazioni.

### Verdict `not_usable`

Uno dei seguenti basta:

```text
critical failures >= 1
high severity failures >= 3
< 60% eventi con verdict pass o caveat
halt/suspension o delisting rappresentati come trading normale in modo non rilevabile
campione non costruibile da fonti indipendenti
```

Con `not_usable`:

```text
NO TRIAL-XMOM-001
NO NEW SMALL-CAP TRIAL WITH YFINANCE DAILY DATA
CONSIDER PROVIDER CHANGE OR DIFFERENT CATEGORY / NEGATIVE CONTROL
```

## Output atteso dell'audit

L'esecuzione futura dovra' produrre un report separato con:

- tabella eventi;
- fonti indipendenti;
- risultato per proprieta';
- failure examples;
- verdict finale `usable`, `usable_with_caveats` o `not_usable`;
- raccomandazione su provider/dataset;
- impatto su `TRIAL-XMOM-001`.

Nome suggerito:

```text
Report-Small-Cap-Data-Quality-Audit-Result-YYYY-MM-DD.md
```

## Template tabella eventi

| Event ID | Ticker | Event date | Category | Independent source | Window | Key check | Severity | Verdict |
|---|---|---:|---|---|---|---|---|---|
| DQ-001 | TBD | TBD | delisting/suspension | TBD | T-10..T+10 | availability/tradability | TBD | TBD |
| DQ-002 | TBD | TBD | reverse split | TBD | T-60..T+60 | adjustment integrity | TBD | TBD |
| DQ-003 | TBD | TBD | halt | TBD | T-10..T+10 | halt visibility | TBD | TBD |
| DQ-004 | TBD | TBD | corporate action | TBD | T-10..T+10 | OHLCV distortion | TBD | TBD |
| DQ-005 | TBD | TBD | offering/dilution | TBD | T-10..T+10 | gap/news representation | TBD | TBD |

## Sequenza operativa futura

1. Compilare la lista eventi da fonti indipendenti.
2. Congelare la lista eventi nel report di audit prima di scaricare dati `yfinance`.
3. Scaricare o ispezionare dati `yfinance` solo dopo congelamento lista.
4. Valutare ogni evento secondo le proprieta' definite qui.
5. Assegnare verdict finale.
6. Solo se `usable` o `usable_with_caveats`, passare al Methodology Gate document.

## Stato dopo questa spec

```text
DATA QUALITY AUDIT SPEC: PRE-REGISTERED
DATA QUALITY AUDIT RESULT: NOT EXECUTED
METHODOLOGY GATE: NOT COMPLETED
TRIAL-XMOM-001: NOT AUTHORIZED
```

Vedi [[Report-Small-Cap-Data-Quality-Gate-Decision-2026-05-14]], [[2026-05-14-cascade-small-cap-data-quality-audit-spec]], [[Roadmap-Master]], [[backlog]], [[Project-Handoff]].
