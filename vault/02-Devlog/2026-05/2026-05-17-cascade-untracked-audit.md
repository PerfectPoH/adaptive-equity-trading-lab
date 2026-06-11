# 2026-05-17 - Untracked audit

## Contesto

Dopo la chiusura del programma NCTRL, il working tree mostrava ancora due percorsi untracked: `.windsurf/` e `data/`.

## Audit read-only

- `.windsurf/workflows/review.md`: workflow locale di code review, senza segreti.
- `data/news/`: vuota.
- `data/snapshots/`: vuota.
- `data/*.csv`: piccoli file metadata/smoke con colonne `symbol`, `market_cap`, `is_etf` e diagnostiche `symbol,status,reason`.

## Referenze trovate

Alcuni CSV sono referenziati da devlog/report storici. `data/small_cap_metadata_eligible_subset30_20260511.csv` e' anche default path in `src/experiments/small_cap_rankex_trial_001.py`.

## Decisione

Versionare i piccoli CSV archivistici e il workflow `.windsurf/workflows/review.md`. Non contengono segreti o dati personali e riducono il rischio di riferimenti rotti nei report storici.

## Nota governance

Versionare questi metadata non riapre i trial small-cap e non cambia il data-quality gate: restano input archivistici/metodologici, non evidenza investibile.


Vedi [[Devlog-Index]] e [[Stato-Corrente]].
