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
- Analisi per-run: distinguere strategia scarsa da strategia troppo selettiva.
- News GDELT laggate di un giorno: usare come contesto sperimentale, non come trigger.

## Comandi stabili

```powershell
.\.venv-lab\Scripts\python.exe -m pytest
.\.venv-lab\Scripts\python.exe -m src.pipeline
.\.venv-lab\Scripts\python.exe -m src.experiments.news_ablation
.\.venv-lab\Scripts\python.exe -m src.experiments.threshold_validation
.\.venv-lab\Scripts\python.exe -m src.experiments.calibration_comparison
.\.venv-lab\Scripts\streamlit.exe run dashboard/app.py
```

## Risultato importante 2026-05-08

Run default `20260508_175742`:

- config: `use_news=false`, `model_probability > 0.55`;
- 119 segnali totali nel 2024;
- 109 segnali eseguibili;
- 10 segnali saltati per `entry_bar_exit_touch`;
- segnali su 9 simboli su 10;
- 9 simboli su 10 sotto buy-and-hold;
- media strategia circa 3.21%;
- buy-and-hold medio circa 48%;
- diagnosi: soglia 0.55 riduce il collo di bottiglia del modello, ma la strategia resta molto sotto buy-and-hold.
- trade analysis: 36 trade chiusi, 23 vincenti, 13 perdenti, win rate trade circa 63.9%;
- best trade: NVDA segnale 2024-02-22, circa +12.79%;
- worst trade: NVDA segnale 2024-06-12, circa -6.89%;
- AMD e' l'unico simbolo con media trade negativa nel run corrente.
- feature-regime analysis:
  - nessun bucket feature e' netto negativo;
  - regime piu' debole: `signal_distance_from_20d_high = mid`, avg return circa 0.30%, loss rate 50%;
  - altri regimi con loss rate 50%: `signal_distance_from_20d_high = high`, `signal_atr_pct = high`;
  - contrasto principale: i trade perdenti hanno volume relativo piu' basso dei trade vincenti;
  - decisione: non aggiungere filtri hard ancora, prima fare esperimento separato su volume/distance/ATR.

Calibration:

- il modello e' overconfident;
- `model_probability > 0.55` funziona come filtro/ranking, non come probabilita' reale;
- calibration layer isotonic fit solo su validation implementato;
- test Brier migliora da circa 0.208 a circa 0.169;
- test mean absolute calibration error migliora da circa 0.212 a circa 0.018;
- soglia raw `0.55` con modello calibrato produce 0 segnali perche' cambia scala probabilistica;
- soglia calibrata `0.25` produce segnali, ma strategy return scende a circa 2.00% contro 3.21% raw;
- decisione: calibrazione utile per interpretazione del rischio, non default operativo.

News ablation:

- `no_news` batte `news` nel backtest 2024 corrente;
- news migliora validation ROC AUC, ma peggiora leggermente test ROC AUC e strategy return;
- verdict: `mixed_or_inconclusive`;
- decisione: tenere news come feature sperimentale, non default.

## Convenzioni Vault

### Devlog

Percorso:

```text
02-Devlog/YYYY-MM-DD-<agente>-<topic>.md
```

### Bug report

Bug aperti in [[backlog]]. Usare `BUG-NNN`, `RISK-NNN` o `TECH-DEBT-NNN`.

### Report

Percorso:

```text
04-Documentazione/Report-<topic>-YYYY-MM-DD.md
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
