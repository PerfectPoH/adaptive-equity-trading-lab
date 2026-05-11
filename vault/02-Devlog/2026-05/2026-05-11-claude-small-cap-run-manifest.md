---
tipo: devlog
data: 2026-05-11
agente: claude
topic: small-cap-run-manifest
tags: [devlog, small-cap, run-manifest, reproducibility, risk-023]
---

# 2026-05-11 - Small-Cap Run Manifest

## Contesto

Il devlog `2026-05-10-cascade-small-cap-critical-diagnostics-roadmap` ha indicato come prossimo gate bloccante il run manifest small-cap, prima di qualunque sweep ulteriore su scanner/execution/portfolio. La motivazione e' RISK-023 (overfitting manuale non tracciato): senza `run_id`, `config_hash` e parametri completi, future iterazioni rischiano di diventare data-mining senza che sia possibile in seguito calcolare Deflated Sharpe Ratio o Probability of Backtest Overfitting.

La Milestone 3B aveva un unico task non spuntato sulla roadmap (`Run manifest small-cap`), ed e' lo stesso oggetto richiamato dal verdetto della smoke portfolio diagnostics del 10 maggio.

## Cosa e' cambiato

Modulo nuovo `src/experiments/run_manifest.py`:

```text
RunManifest dataclass frozen con campi:
- run_id (uuid breve auto-generato se non fornito)
- config_hash (SHA-256 deterministico)
- created_at (ISO 8601 UTC se non fornito)
- schema_version ("1")
- config (rappresentazione JSON-serializable di tutta la SmallCapHistoricalRunConfig nested)
- universe (lista simboli)
- period {start, end} (date string)
- git_commit (best-effort via subprocess; None se git non disponibile)
- host (best-effort via socket; None se rilevazione disabilitata o fallisce)
- extras (dict libero per metadati non strutturati)

compute_config_hash(config) -> str:
- normalizza dataclass annidati, dict, sequenze, Path, datetime;
- serializza con json.dumps(sort_keys=True, separators=(",", ":"));
- hashing SHA-256 hex.

build_run_manifest(config, ...) -> RunManifest:
- tutti i campi context-dependent (run_id, created_at, git_commit, host) accettano valori espliciti;
- detect_git e detect_host opzionali per riproducibilita' nei test.

write_run_manifest_json(manifest, path) -> Path:
- file JSON sort_keys + indent=2, encoding utf-8, newline finale stabile.
```

Integrazione nel runner storico `src/experiments/small_cap_historical_runner.py`:

```text
run_small_cap_historical_report() ora:
- estrae universe dai metadata candidati (deduplica preservando l'ordine);
- ricava period_start/period_end dalle as_of date risolte;
- costruisce il manifest con build_run_manifest(config, ...);
- scrive run_manifest.json accanto agli altri artefatti;
- include run_manifest nel dict ritornato e in paths;
- passa il manifest a write_small_cap_backtest_report_markdown.
```

Integrazione nel report `src/analysis/small_cap_backtest_report.py`:

```text
build_small_cap_backtest_report / write_small_cap_backtest_report_markdown:
- nuovo parametro opzionale run_manifest (dict);
- la chiave 'run_manifest' viene aggiunta al report dict;
- _to_markdown emette una nuova sezione '## Run Manifest' in testa, prima del Verdict, con run_id, config_hash, schema_version, created_at, period, universe, git_commit e host.
```

## Verifiche

```text
python3 -m pytest tests/test_run_manifest.py -v
13 passed
```

Coverage del modulo isolato:

```text
- compute_config_hash deterministico su dataclass annidati e dict;
- hash cambia al variare di un parametro (anche nested);
- hash invariante rispetto all'ordine delle chiavi del dict;
- compatibilita' con Path e dataclass annidati senza eccezioni;
- run_id auto-generato con prefisso run_ e contenuto non vuoto;
- nested dataclass serializzati ricorsivamente;
- detect_git=False / detect_host=False producono campi None deterministici;
- extras preservato come dict;
- manifest_to_dict round-trip;
- write_run_manifest_json scrive file con newline finale, sort_keys, schema versionato;
- due run con stessa config differiscono solo su run_id e created_at.
```

Integrazione runner:

```text
python3 -m pytest tests/test_run_manifest.py tests/test_small_cap_historical_runner.py tests/test_small_cap_backtest_report.py -v
27 passed
```

I tre nuovi test del runner verificano: scrittura di run_manifest.json con campi attesi (run_id, config_hash, universe, period, git_commit, host, schema_version) e presenza della sezione `## Run Manifest` nel markdown; determinismo del config_hash fra due run con stessa config ma run_id/created_at diversi; cambio dell'hash quando un solo parametro della config viene modificato (`primary_benchmark`).

Full suite:

```text
python3 -m pytest
148 passed, 670 warnings
```

Si parte dai 132 passed della smoke 10/05 e si arriva a 148: 16 test aggiunti, nessuna regressione sui test esistenti. I warning sono FutureWarning di pandas preesistenti, nessuno introdotto da questo lavoro.

## Risultati

Ogni run del runner storico small-cap ora produce un manifest tracciabile. Esempio di campi serializzati per una stessa configurazione su due run diversi:

```text
run A: run_id=run_a, config_hash=<H>, created_at=2026-05-11T00:00:00+00:00
run B: run_id=run_b, config_hash=<H>, created_at=2026-05-11T01:00:00+00:00
```

Con `<H>` identico fra A e B. Una modifica a un solo parametro della config produce un hash diverso, quindi sweep ripetuti sulla stessa configurazione sono identificabili e separabili da sweep su configurazioni distinte. Il manifest e' embedded anche nel markdown del report, in testa, quindi un report letto da un agente futuro mostra subito run_id e config_hash senza richiedere file aggiuntivi.

## Decisione

RISK-023 passa da `aperto` a `mitigato` nel backlog. Milestone 3B vede il task `Run manifest small-cap` spuntato; il gate metodologico viene aggiornato di conseguenza in `Roadmap-Master`.

## Prossima mossa

Il devlog 10/05 critical-diagnostics-roadmap indica come passo successivo, ora che il manifest esiste:

1. Ripetere la smoke su watchlist piu' ampia e piu' periodi, in modo che lo Score Profile abbia abbastanza bucket per misurare la monotonicita' di `small_cap_scanner_score` (RISK-021).
2. Aggiungere un confronto ex-outlier: `portfolio_return` ricalcolato senza top 1 / top 3 trade per parlare di robustezza (RISK-022).
3. Solo dopo: sector cap, random delay, survivorship sensitivity, opening regime check.

Non introdurre ancora sweep su scanner/execution/portfolio: il manifest registra i tentativi ma non e' un'autorizzazione a moltiplicarli.

## Note metodologiche

- `git_commit` e `host` sono best-effort: se `git` non e' nel PATH o `socket.gethostname` fallisce, restano `None`. I test lo verificano esplicitamente disattivando la rilevazione, per garantire manifest stabili.
- `config_hash` e' SHA-256 hex sulla rappresentazione JSON canonicalizzata (sort_keys, separatori compatti). Path vengono convertiti in stringa, datetime/timestamp via `.isoformat()`. Questo lo rende stabile fra interpreti diversi e fra Windows/Linux.
- `schema_version="1"` documentato per future evoluzioni dello schema senza rompere agenti che leggono `run_manifest.json`.

## Relazioni

Vedi [[Roadmap-Master]], [[backlog]], [[2026-05-10-cascade-small-cap-critical-diagnostics-roadmap]], [[2026-05-10-cascade-small-cap-portfolio-diagnostics-smoke]], [[small-cap-swing-research-spec]].
