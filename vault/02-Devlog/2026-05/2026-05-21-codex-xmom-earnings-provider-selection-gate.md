# 2026-05-21 - XMOM earnings provider selection gate

## Contesto

Dopo i guardrail earnings extraction, serviva una gate separata per selezionare la fonte dati earnings calendar senza implementare ancora l'extractor.

## Cosa e' stato fatto

Creato:

```text
experiments/provider_aware_research/xmom_earnings_provider_selection_gate_20260521
src/experiments/xmom_earnings_provider_selection_validator.py
tests/test_xmom_earnings_provider_selection_validator.py
```

## Risultato

```text
EARNINGS_PROVIDER_SELECTION_GATE_PASS
passed: 39
failed: 0
```

Test mirati:

```text
6 passed
```

## Decisione

Il provider-selection gate e' valido ma non interrogato.

Blocco ancora valido:

```text
no provider query
no extractor
no market-data download
no OOS
no paper/live
no promotion
```

Vedi [[Report-XMOM-Earnings-Provider-Selection-Gate-2026-05-21]].
