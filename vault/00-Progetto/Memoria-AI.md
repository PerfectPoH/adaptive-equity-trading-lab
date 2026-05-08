---
tipo: memoria-ai
progetto: adaptive-equity-trading-lab
ultimo-aggiornamento: 2026-05-08
tags: [memoria, anti-pattern, best-practice, agenti]
---

# Memoria Condivisa AI

Questo file serve a non rifare gli stessi errori. Prima di modificare codice, strategia, feature, label, backtest o documentazione importante, leggere questa pagina.

## Contesto stabile

- Il progetto e' un laboratorio personale di trading quantitativo.
- La Milestone 1 e' una pipeline MVP, non una strategia pronta.
- Il primo backtest 2024 non batte buy-and-hold.
- Questo risultato e' accettabile perche' la pipeline dimostra onesta' metodologica.
- Qualsiasi agente deve separare prototipo, ricerca, paper trading e live trading.

## Errori da NON ripetere

### Dati

- Non trattare `yfinance` come fonte istituzionale.
- Non ignorare dataset vuoti, ticker troncati o colonne mancanti.
- Non salvare snapshot corrotti.
- Non usare dati scaricati oggi come prova storica point-in-time.
- Non dimenticare survivorship bias.

### Feature e label

- Non fare scaling sull'intero dataset prima dello split temporale.
- Non usare random split su serie temporali.
- Non calcolare feature con dati futuri.
- Non generare label prima di aver separato train, validation e test.
- Non usare il close dello stesso giorno come entry eseguibile.
- Non spostare segnali di un giorno senza test espliciti.
- Non permettere a dati 2024 di influenzare feature o scaler del train.

### Backtest

- Non interpretare backtesting.py come simulatore realistico di mercato.
- Non assumere fill perfetti senza slippage e commissioni.
- Non ignorare gap overnight.
- Non dire "batte il mercato" se non batte buy-and-hold out-of-sample.
- Non cambiare parametri dopo aver visto il test senza loggare l'esperimento.

### Risk e live trading

- Non collegare un broker live in Milestone 1.
- Non usare leva.
- Non fare short nella fase iniziale.
- Non rimuovere stop loss.
- Non aumentare size per recuperare perdite.
- Non confondere paper trading con live trading.

### Codice e ambiente

- Su questo PC `python` puo' puntare allo stub Microsoft Store. Usare `.venv-lab`.
- La venv stabile e' `.venv-lab`.
- `.venv` e' una venv parziale/da ripulire quando Windows la libera.
- Non committare snapshot pesanti, cache o ambienti virtuali.
- Non mischiare modifiche a Soresina con questo repo.

### Vault

- Il vault deve restare leggibile da umani.
- Non buttare output generato dentro il vault se e' solo cache.
- Graphify, quando arrivera', deve stare fuori dal vault come artefatto generato.
- Ogni nuova nota deve collegarsi con wikilink almeno a un documento vivo.

## Cose fatte bene da ricordare

- MVP piccolo e costruibile.
- Test anti-lookahead scritti subito.
- Snapshot con hash.
- Entry al next open.
- Label builder separato.
- Split temporale chiaro.
- Experiment log obbligatorio.
- Dashboard minima.
- Fallimento rispetto a buy-and-hold documentato invece di nascosto.
- Vault separato e pulito, non copiato dal progetto Soresina.
- Test anti-shift su `backtesting.py`: il trade deve entrare al next open.
- Purged temporal split: eliminare le ultime barre dei periodi quando la label forward supererebbe il confine.
- Analisi per-run: distinguere strategia scarsa da strategia troppo selettiva.
- News GDELT laggate di un giorno: usare come contesto sperimentale, non come trigger.
- Snapshot fallback: se `yfinance` fallisce, usare l'ultimo snapshot locale valido invece di cambiare universo in modo silenzioso.

## Comandi stabili

```powershell
.\.venv-lab\Scripts\python.exe -m pytest
.\.venv-lab\Scripts\python.exe -m src.pipeline
.\.venv-lab\Scripts\python.exe -m src.experiments.news_ablation
.\.venv-lab\Scripts\python.exe -m src.experiments.threshold_validation
.\.venv-lab\Scripts\python.exe -m src.experiments.calibration_comparison
.\.venv-lab\Scripts\python.exe -m src.experiments.regime_filter_validation
.\.venv-lab\Scripts\python.exe -m src.experiments.walk_forward_validation
.\.venv-lab\Scripts\python.exe -m src.experiments.model_comparison
.\.venv-lab\Scripts\python.exe -m src.experiments.feature_set_comparison
.\.venv-lab\Scripts\python.exe -m src.experiments.target_exit_comparison
.\.venv-lab\Scripts\streamlit.exe run dashboard/app.py
```

## Risultato importante 2026-05-08

Run default `20260508_192713`:

- config: `use_news=false`, `model_type=random_forest`, feature set baseline, isotonic calibration, `model_probability > 0.25`, target/exit default `1.5 ATR stop / 3 ATR take-profit / 10d timeout`, no regime filters;
- default scelto tramite walk-forward: raw 0.50 nel fold 2023, isotonic 0.25 nel fold 2024;
- 1093 segnali totali nel 2024;
- 1036 segnali eseguibili;
- 57 segnali saltati per `entry_bar_exit_touch`;
- segnali su 10 simboli su 10;
- 9 simboli su 10 sotto buy-and-hold;
- media strategia circa 6.49%;
- buy-and-hold medio circa 48%;
- diagnosi: timeout e finalizzazione dei trade a fine finestra sono ora coerenti col target; resta molto sotto buy-and-hold;
- trade analysis: 193 trade chiusi, 105 vincenti, 88 perdenti, win rate trade circa 54.4%;
- best trade: TSLA segnale 2024-11-06, circa +19.65%;
- worst trade: TSLA segnale 2024-07-12, circa -12.12%;
- nessun simbolo ha media trade negativa nel run corrente.
- feature-regime analysis:
  - nessun bucket feature e' netto negativo;
  - regime piu' debole: `signal_rolling_volatility_20d = low`, avg return circa 0.38%, loss rate circa 53.2%;
  - altri regimi fragili: `signal_distance_from_20d_high = high`, `signal_model_probability = low`;
  - contrasto principale: i trade perdenti hanno volume relativo leggermente piu' alto dei trade vincenti;
  - esperimento separato su volume/distance/ATR eseguito;
  - verdict: `filters_did_not_help`;
  - baseline calibrata 0.25 resta migliore dei filtri hard provati in quell'esperimento;
  - combined filters migliorano max drawdown ma scendono a circa 3.36% strategy return;
  - decisione: nessun regime filter diventa default; combined filters solo possibile modalita' risk-first futura.

Walk-forward:

- runner: `src.experiments.walk_forward_validation`;
- fold `wf_2023`: validation 2022 -> raw threshold 0.50 -> test 2023 strategy return circa 3.48%;
- fold `wf_2024`: validation 2023 -> isotonic threshold 0.25 -> test 2024 strategy return circa 6.49%;
- mean test strategy return circa 5.01%;
- mean test excess return circa -69.72%;
- fold che battono buy-and-hold: 0/2;
- verdict: `positive_but_under_benchmark`;
- decisione: default di ricerca promosso a isotonic threshold 0.25.
- nota anti-overfit: raw threshold 0.50 e altri valori migliori nel test-window sweep non diventano default se non scelti in walk-forward.

Model comparison:

- runner: `src.experiments.model_comparison`;
- modelli confrontati: `logistic_regression`, `random_forest`, `hist_gradient_boosting`;
- min validation trades: 30, per evitare scelte su campioni minuscoli;
- fold `wf_2023`: selezionato default target/exit + `baseline` + `random_forest`, raw threshold 0.45 -> test 2023 strategy return circa 6.50%;
- fold `wf_2024`: selezionato default target/exit + `baseline` + `random_forest`, isotonic threshold 0.25 -> test 2024 strategy return circa 6.49%;
- mean test strategy return circa 6.50%;
- fold che battono buy-and-hold: 0/2;
- decisione: non cambiare default modello; Random Forest resta default.

Feature set comparison:

- runner: `src.experiments.feature_set_comparison`;
- feature set confrontati: `baseline`, `enhanced_context`;
- enhanced context aggiunge momentum piu' lungo, slope EMA, range intraday, posizione nel range 20d, volume z-score, dollar-volume e contesto SPY;
- min validation trades: 30;
- fold `wf_2023`: selezionato `baseline`, raw threshold 0.45 -> test 2023 strategy return circa 6.50%;
- fold `wf_2024`: selezionato `baseline`, isotonic threshold 0.25 -> test 2024 strategy return circa 6.49%;
- mean test strategy return circa 6.50%;
- fold che battono buy-and-hold: 0/2;
- decisione: non promuovere `enhanced_context`; baseline resta selezionato dopo timeout-consistent backtesting.

Target/exit comparison:

- runner: `src.experiments.target_exit_comparison`;
- configurazioni confrontate: default `1.5x/3x/10d`, fast `1x/2x/5d`, balanced `1.5x/2.25x/10d`, patient `2x/4x/15d`;
- fold `wf_2023`: selezionato default raw 0.45 -> test 2023 strategy return circa 6.50%;
- fold `wf_2024`: selezionato balanced isotonic 0.35 -> test 2024 strategy return circa 6.36%;
- mean test strategy return circa 6.43%;
- fold che battono buy-and-hold: 0/2;
- decisione: non promuovere `balanced`; viene scelto in validation ma resta leggermente sotto il default 2024.

Calibration:

- il modello e' overconfident;
- raw `model_probability` funziona come filtro/ranking, non come probabilita' reale;
- calibration layer isotonic fit solo su validation implementato;
- test Brier migliora da circa 0.208 a circa 0.172;
- test mean absolute calibration error migliora da circa 0.207 a circa 0.042;
- soglia `0.45` con modello calibrato produce 0 segnali perche' cambia scala probabilistica;
- soglia calibrata `0.25` produce 1093 segnali e strategy return circa 6.49% dopo timeout-consistent backtesting;
- decisione: calibrazione isotonic 0.25 e' default di ricerca, ma non prova di strategia pronta.

News ablation:

- `no_news` batte `news` nel backtest 2024 corrente;
- news migliora validation ROC AUC, ma peggiora leggermente test ROC AUC e strategy return;
- verdict: `mixed_or_inconclusive`;
- decisione: tenere news come feature sperimentale, non default.

## Convenzioni Vault

Prima di creare o spostare note, leggere [[Vault-Structure]].

### Devlog

Percorso:

```text
02-Devlog/YYYY-MM/YYYY-MM-DD-<agente>-<topic>.md
```

### Bug report

Bug aperti in [[backlog]]. Usare `BUG-NNN`, `RISK-NNN` o `TECH-DEBT-NNN`.

### Report

Percorso:

```text
04-Documentazione/Reports/Report-<topic>-YYYY-MM-DD.md
```

## Routine ogni sessione

1. Leggere [[INDEX]].
2. Leggere [[Protocollo-Collaborazione]].
3. Controllare [[backlog]].
4. Fare lavoro piccolo e verificabile.
5. Eseguire test se si tocca codice.
6. Aggiornare devlog.
7. Aggiornare report o roadmap se cambia lo stato.

Vedi anche [[Regole-Quant]] e [[Regole-Codice]].
