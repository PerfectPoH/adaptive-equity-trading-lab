---
tipo: report
progetto: adaptive-equity-trading-lab
data: 2026-06-11
tags: [audit, backtest, overfitting, p-hacking, motore, metodologia]
---

# Report - Audit Esterno Motore e Metodologia (2026-06-11)

Audit indipendente dell'intero progetto: motore MVP large-cap, Portfolio Studio / OOS validation, regime classifier, true-ETF backtest, suite di test. Include verifiche numeriche riprodotte sugli artifact reali.

Vedi [[Stato-Corrente]] e [[Memoria-AI]].

## Verdetto sintetico

Il motore **non bara intenzionalmente** e la cultura metodologica (preregistrazione, DSR, gate, report onesti) e' sopra la media. Ma due risultati headline sono **sopravvalutati per ragioni strutturali**, non per bug:

1. Il gate `BEATS_STATIC` dello Studio OOS e' vinto in gran parte da un artefatto dei cost tier, non da skill di selezione per regime (quantificato sotto).
2. La multiplicita' dichiarata (trial_count=2) e' molto sotto quella reale di programma; il vostro stesso `dsr_by_trial_count` mostra che il risultato non regge oltre ~3-5 look.

Il percorso piu' pulito del lab e' `true_etf_backtest` (segnali causali, cash accounting reale): e' la direzione giusta.

## A. Verifiche superate (il motore non bara qui)

- 823 test passano (i moduli esclusi falliscono solo per Python 3.10 del sandbox / dipendenze opzionali, non per bug).
- Entry al next open verificata: `entry_price = Open.shift(-1)`, runner usa limit = next open su `backtesting.py`.
- Feature tutte backward-looking: rolling con `min_periods`, nessuna finestra centrata, news GDELT laggate di 1 giorno, `spy_trend_positive` calcolato al close del giorno segnale.
- Purged temporal split + embargo implementati e testati; test anti-mutazione del futuro presente.
- `classifier_exposure_series` e `kronos_exposure_series` usano `date < period` (strettamente prima): nessun leak same-day nell'overlay difensivo.
- Regime classifier deterministico, solo finestre trailing, hysteresis: niente fitting in-sample.
- Implementazione DSR/PSR corretta (formule Lopez de Prado), `expected_maximum_sharpe_ratio` corretto.
- `.env` correttamente git-ignored.

## B. Problemi trovati

### B1. Studio OOS: il gate BEATS_STATIC e' strutturalmente sbilanciato (ALTO)

Verifica numerica riprodotta sul pool reale (108 componenti, cutoff 2025-01-01, vol-norm):

```text
Distribuzione costi pool: 100bps: 26, 200: 1, 350: 1, 375: 14, 500: 66
  -> ~76% del pool sono varianti factory deliberatamente cost-crippled.

Somma ritorni OOS media per fascia di costo:
  100bps: +8.27   375bps: -3.49   500bps: -2.01

OOS 2025: dynamic regime-routed (report 005):  +49.6%
          static SOLO componenti <=100bps:      +29.2%
          static tutti (usata nel gate):        -22.9%
```

La baseline static (-22.9%) e' dominata da cloni della stessa strategia con 375-500bps di costi. Con una baseline onesta a parita' di costi, il delta del routing scende da **+72.5pp a ~+20pp**. Il gate misura in gran parte "selezionare i componenti a costi bassi", che banalmente persiste OOS.

### B2. Duplicati nel pool (ALTO, collegato a B1)

12 componenti su 104 hanno stream di ritorni **identici** a un altro. La regola unconditional top-5 Sharpe IS seleziona 4 stream identici a 500bps (risultato OOS -0.6%: selezione degenerata). I duplicati contaminano: baseline static, matrice di correlazione, `sharpe_std` cross-section usata dal DSR.

### B3. Multiplicita' reale >> dichiarata (ALTO)

`dsr_by_trial_count` del run 005: trial=2 -> 0.99999; trial=5 -> 0.503; trial=10 -> 0.008. I trial 001-004 hanno preceduto il "preregistered" 005 nella stessa sessione, il protocollo e' evoluto dopo aver visto l'OOS (vol-norm introdotta dopo il sign-flip del 002), e gli stessi cutoff 2024/2025 sono stati riusati in decine di esperimenti del programma. Il report lo ammette onestamente, ma il verdetto headline `DSR_PASS` resta calcolato a trial_count=2. Accounting onesto: il risultato 005/006 **non passa** il DSR a multiplicita' di programma.

### B4. Selection bias della libreria componenti (ALTO, gia' noto come "pool sopravvissuto")

Troncare gli stream al cutoff non rimuove il bias di QUALI componenti esistono: la libreria workbench e' stata salvata/curata nel 2026 conoscendo il 2024-2025. Qualunque selezione su quel pool eredita il senno di poi. Conseguenza: i numeri del house trial (+35.8%/-2.8% DD 2025, +66.8%/-4.3% 2024) sono su stream proxy vol-normalizzati da un pool curato col futuro noto — utili come diagnostica dell'engine, non come stima di edge. Rischio principale: ancoraggio psicologico a quei numeri.

### B5. MVP: `entry_bar_exit_touch` e' un look-ahead (MEDIO, documentato ma da correggere)

`label_builder` e `execution` saltano il trade se High/Low **del giorno di entry** tocca TP o SL: informazione intraday non disponibile all'open. Non e' "conservativo": rimuove anche gli stop-out immediati (bias favorevole). 57 segnali saltati nel run default 2024. La strategia simulata non e' implementabile live cosi' com'e'.

### B6. MVP: problemi minori

- Sizing su equity fissa 100k mentre il cash del backtest evolve (size puo' eccedere il cash disponibile o restare sottodimensionata).
- Timeout off-by-one: label esce al Close di entry+9, runner all'Open di entry+10 (documentato nel codice).
- Benchmark buy-and-hold su Close raw esclude i dividendi (per SPY ~1.5%/anno): usare Adj Close/total return per il confronto.
- Aggregato = media dei backtest per-simbolo: assume capitale separato per ogni simbolo, non e' un portafoglio.
- Universo = 8 mega-cap vincitrici scelte col senno di poi + SPY/QQQ (gia' documentato come survivorship: di fatto e' il controllo negativo).

### B7. Stream proxy: metriche non comparabili (MEDIO)

Le date degli stream componenti sono le entry date dei trade; lo "Sharpe daily" e il max DD calcolati su quelle serie (trade-day + zeri) non sono confrontabili con metriche di mercato. La vol-norm con `max_scale=100` produce il +1296% del trial 007 (gia' flaggato come non rappresentativo, bene).

### B8. Codice / sistema (BASSO)

- `experiments/databento_probe_one_event.py` riga 363: backslash dentro f-string -> SyntaxError su Python <3.12. Portabilita'.
- 2 test falliti in `.pytest_cache/lastfailed` (`test_lab_dashboard_data`, `test_dashboard_app_bootstrap`): da sistemare o aggiornare.
- `temporal_split` ha `embargo_days=0` di default: meglio un default >0.
- ANOVA p-value approssimato (Wilson-Hilferty) nel regime classifier: ok per ordinamento, dichiararlo nei report che lo citano.

## C. Risposte alle domande dell'audit

**Il motore bara?** No sui fondamentali (entry next-open, feature causali, split puliti, overlay senza leak). Si' in un punto del MVP (`entry_bar_exit_touch`, documentato) e — piu' importante — il gate dynamic-vs-static dello Studio e' una corsa truccata strutturalmente (B1+B2), senza intenzione.

**C'e' overfitting / p-hacking?** Non nella forma classica (gli sweep sono governati, i default non vengono promossi senza walk-forward). Il rischio reale e' piu' sottile: libreria di componenti curata col senno di poi (B4), multiplicita' di programma non contabilizzata (B3), baseline deboli (B1), riuso degli stessi anni OOS in decine di esperimenti. Il congelamento del protocollo con replica mensile e' la contromisura giusta: **l'unica evidenza pulita sara' la replica su dati nuovi.**

## D. Suggerimenti per migliorare il motore (in ordine di valore)

1. **Baseline oneste nel gate Studio**: (a) static a parita' di cost tier; (b) top-k unconditional dopo dedup; (c) permutation test: shuffla le label di regime e ricalcola il delta dynamic-static N volte -> p-value empirico del valore aggiunto del routing. Solo (c) dimostra skill di regime.
2. **Dedup del pool**: hash dello stream di ritorni, escludere duplicati da selezione, baseline, correlazioni e sharpe_std del DSR (test automatico nel gate panel).
3. **Trial counter automatico di programma**: contare i run reali (es. directory in `experiments/runs/` per famiglia di trial) e passare quel numero al DSR invece di costanti dichiarate. `effective_trial_count` esiste gia': collegarlo.
4. **Fix `entry_bar_exit_touch`**: sostituire con regola implementabile (es. niente skip; stop/TP attivi dal giorno di entry con regola conservativa stop-first, che gia' avete) e rerun della baseline MVP per quantificare l'impatto.
5. Sizing dal cash corrente nel runner MVP; benchmark su total return (Adj Close).
6. Promuovere `true_etf_backtest` a motore riusabile unico (cash accounting causale) e migrare li' ogni nuovo trial; lasciare gli stream proxy solo come diagnostica UI etichettata in "unita'".
7. Fix portabilita' f-string (3.10/3.11), fix dei 2 test dashboard, default `embargo_days>0`.

## E. Suggerimenti per trovare la strategia

1. **Non toccare il protocollo congelato**: la replica mensile su mesi nuovi e' il test piu' informativo che avete. Definire PRIMA il criterio di successo (es. quanti mesi, quale soglia) per non giudicare a posteriori.
2. **Procedere con TRUE-ETF-003 (opzione a)**: universo ~50 ETF e' la strada con il miglior rapporto evidenza/costo — niente survivorship serio, costi noti, dati gratuiti adeguati. Comprare il data bundle small-cap solo se la famiglia ETF mostra segnale.
3. **Il vostro asset validato e' la difesa, non l'attacco**: il regime classifier ha 2 validazioni OOS come overlay. Una strategia "ETF semplici + risk overlay del classifier" e' un candidato a se', testabile nel motore true con multiplicita' 1 reale.
4. Per nuovi candidati alpha privilegiare anomalie con timestamp certi e struttura (eventi SEC con orario, term structure, regime-conditional exposure) rispetto a ML su feature tecniche di mega-cap: quel controllo negativo l'avete gia' fatto bene.
5. Qualsiasi ritorno alle small-cap richiede prima dati PIT con delisted (Norgate/Sharadar): senza, ogni risultato e' inammissibile per costruzione (gia' vostra policy, confermata).

## Artifact delle verifiche

Verifiche numeriche eseguite ricostruendo il pool con `load_portfolio_lab_components(limit=60) + build_strategy_factory_components(max_variants=48)`, cutoff 2025-01-01, vol-norm con config OOS-005. Run citati: `studio_oos_005_20260611_113945`, `house_trial_001_20260611_120842`.
