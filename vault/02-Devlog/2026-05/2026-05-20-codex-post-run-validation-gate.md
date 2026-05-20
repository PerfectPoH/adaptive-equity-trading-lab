# 2026-05-20 - Post-run validation gate

## Contesto

Dopo il bounded provider-aware replay e il nuovo `XMOM` pre-run gate, mancava un controllo post-run che validasse gli artifact completati prima di interpretazione o promozione.

Il gate non deve cercare profitti. Deve verificare coerenza interna, execution guardrails e riconciliazione contabile.

## Cosa e' cambiato

Aggiunto validator:

```text
src.experiments.post_run_validation_gate_validator
```

Aggiunti test:

```text
tests/test_post_run_validation_gate_validator.py
```

Aggiunto artifact spec:

```text
experiments/provider_aware_research/post_run_validation_gate_spec_20260520/
```

Aggiunto report:

```text
vault/04-Documentazione/Reports/Report-Post-Run-Validation-Gate-2026-05-20.md
```

## Verifiche

Test mirati:

```text
tests/test_post_run_validation_gate_validator.py -> 5 passed
```

Run reale locale:

```powershell
.\.venv-lab\Scripts\python.exe -m src.experiments.post_run_validation_gate_validator --run-dir experiments\runs\provider_aware_oos_replay_bounded_20260520
```

Risultato:

```text
status: pass
gate_decision: POST_RUN_VALIDATION_PASS
passed: 28
failed: 0
```

## Decisione

Il bounded replay resta non promuovibile come strategia perche' sotto benchmark, ma passa il controllo post-run di integrita' e quindi puo' essere interpretato come run coerente.

## Prossima mossa

Prima di qualunque nuova esecuzione:

1. far passare il pre-run gate specifico;
2. eseguire il run autorizzato;
3. applicare questo post-run gate;
4. solo dopo leggere le metriche di performance e applicare la decision rule pre-registrata.

Vedi [[Report-Post-Run-Validation-Gate-2026-05-20]], [[Project-Handoff]], [[Regole-Quant]].
