# 2026-05-20 - XMOM data ingestion gate

## Contesto

Dopo pre-run e post-run gate, il collo di bottiglia operativo di `TRIAL-XMOM-001` e' il dataset Databento. Prima di permettere al pre-run gate di diventare verde, serve validare il data input come oggetto isolato e immutabile.

## Cosa e' cambiato

Aggiunto validator:

```text
src.experiments.xmom_data_input_validator
```

Aggiunti test:

```text
tests/test_xmom_data_input_validator.py
```

Hardening del pre-run gate:

```text
src.experiments.xmom_pre_run_gate_validator
```

Ora `databento_data_exists` richiede un `data_input_validation_report.json` con `status=pass` e `gate_decision=DATA_INPUT_VALIDATION_PASS`, non una directory con file generici.

Aggiunta spec:

```text
experiments/provider_aware_research/xmom_data_ingestion_gate_spec_20260520/
```

## Verifiche

Test mirati:

```text
tests/test_xmom_data_input_validator.py
tests/test_xmom_pre_run_gate_validator.py
```

Risultato:

```text
10 passed
```

Pre-run gate reale:

```text
status: fail
gate_decision: BLOCKED_EXIT_1
failed check: runtime_databento_data_exists
```

Questo e' atteso: non e' ancora stato ingerito e validato alcun dataset XMOM.

## Decisione

Il progetto ora ha una quarantena dati esplicita. Il prossimo sblocco consentito non e' un backtest, ma la creazione del dataset directory e la generazione del validation report.

Vedi [[Report-XMOM-Data-Ingestion-Gate-2026-05-20]], [[Project-Handoff]], [[Regole-Quant]].
