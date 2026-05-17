# 2026-05-17 - TRIAL-NCTRL-001 property-check result

## Contesto

Dopo il completamento di `RESEARCH-047`, e' stata eseguita una singola run pre-registrata di `TRIAL-NCTRL-001` come methodology negative control. La run non e' un test di alpha e non abilita promozione strategica.

## Cosa e' cambiato

- Aggiunto runner esplicito `experiments/configs/nctrl_trial_001.py` derivato dalla config scaffolding, ma con `trial_accounting` reale `TRIAL-NCTRL-001` e `extras.purpose=nctrl_trial_001_property_check`.
- Aggiunto evaluator P1-P8 in `src/analysis/nctrl_property_evaluator.py`.
- Aggiunta rigenerazione del property report da artifact esistenti, senza rerun.
- Ottimizzato P5 bootstrap precomputando i ritorni holding-window, mantenendo `N=1000` e `base_seed=700`.
- Aggiunto report P6 random-entry sign-flip frequency con 100 simulazioni valide.
- Corretto P2 per accettare la rappresentazione dell'ultimo giorno effettivo `2024-12-27` quando il calendario richiesto finisce a `2024-12-31`.

## Verifiche

- Test mirati: `21 passed` su runner/evaluator/property report/bootstrap/random-entry.
- Run reale completata: `run_nctrl_trial_001_20260517`.
- Property report rigenerato dagli artifact: `overall_status=pass`, P1-P8 pass.

## Risultati

- Output dir: `experiments/runs/nctrl_trial_001_2024_20260517`.
- `config_hash`: `732bce85161b9a00c3799206c081e2a999b7e7ef4053581ce8aa3d0e47b9ecab`.
- Manifest period: `2024-01-02..2024-12-27`.
- Portfolio trades: 32.
- P5: `simulations=1000`, `base_seed=700`, `mean_return=0.009076682644783847`.
- P6: `simulations=100`, `valid=100`, `sign_flip_excluding_top_3_frequency=0.06`.

## Decisione

`TRIAL-NCTRL-001` passa come property-based negative control della macchina di ricerca. Non e' una validazione strategica, non riapre track small-cap archiviati, non autorizza paper trading e non sblocca nuovi trial small-cap con dati `yfinance` daily alone.
