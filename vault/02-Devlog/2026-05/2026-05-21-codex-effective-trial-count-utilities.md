# 2026-05-21 - Effective trial-count utilities

## Contesto

Dopo DSR/PSR e CPCV serviva stimare `N_eff`, cioe' il numero effettivo di trial indipendenti da passare al DSR.

## Cosa e' stato fatto

Creato:

```text
src/validation/effective_trial_count.py
tests/test_effective_trial_count.py
```

## Risultato

```text
9 passed
```

## Decisione tecnica

Metodo primario:

```text
participation_ratio sugli autovalori della matrice di correlazione
```

Metodo di controllo:

```text
average_correlation
```

La regola Kaiser pura non e' usata come primaria perche' su matrice identita' con autovalori esattamente pari a 1 non rispetta l'invariante `identity -> N_eff = N_nominal`.

## Blocco ancora valido

```text
no OOS
no provider query
no sweep
no paper/live
no promotion
```

Vedi [[Report-Effective-Trial-Count-Utilities-2026-05-21]].
