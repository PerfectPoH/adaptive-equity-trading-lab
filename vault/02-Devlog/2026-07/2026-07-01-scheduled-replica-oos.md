---
tipo: devlog
progetto: adaptive-equity-trading-lab
data: 2026-07-01
agente: claude
ultimo-aggiornamento: 2026-07-01
tags: [scheduled-task, replica-mensile, membership, oos, ledger]
---

# Replica mensile OOS congelato - run schedulato #1

Prima esecuzione schedulata post-freeze (protocollo congelato 2026-06-11,
[[Criterio-Preregistrato-Membership-2026-06]]). Letto tutto il criterio con i
tre emendamenti prima di eseguire. Nessuna modifica a codice/parametri/ledger.

## Passi eseguiti

1. `replica_support_checks` — regime history rigenerata
   (`experiments/runs/regime_index_refresh_20260701/`), seam check ripetuto:
   overlap_ratio 0.573 identico all'originale.
2. `studio_oos_runner --cutoff 2025-01-01 --trial-id TRIAL-STUDIO-OOS-REPLICA
   --vol-norm --mode rule --top-k 5` — verdetto
   `OOS_POSITIVE__BEATS_STATIC__OUTLIER_ROBUST__DSR_PASS`,
   `dynamic_total_oos` = 0.496308, bit-identico al freeze.
3. `honest_baselines_trial --extend-streams` — verdetto
   `ROUTING_SKILL_NOT_CONFIRMED__S3` (invariato). Coverage ledger:
   195->393 chiusi, 270->260 pendenti, 0 delisting, 0 quarantene,
   **9 data_revision_warnings** (erano 0 al freeze — yfinance ha riscritto
   la storia di 9 entry; gestito da regola Emendamento 003, nessun impatto
   sul verdetto, ma da monitorare nei prossimi mesi).

## Esito conteggio mesi

`membership_blend_static` (0.4113) e `unconditional_top5` (0.083574) sono
**bit-identici** al run di freeze — esattamente come previsto
dall'Emendamento 001 (holding 90/180d, primi trade post-freeze non chiudono
prima di settembre 2026 / febbraio 2027). Mese 1 di 6: **non contato**.
Delta membership del mese (+32.77pp) invariato rispetto all'in-program
(+32.7pp) per costruzione — nessuna nuova evidenza, solo verifica di
riproducibilita'.

`static_cost_matched` (27.8%->24.88%) e il p-value del permutation test
(0.1393->0.1443) SI muovono (dipendono da stream a holding corto e da
`regime_history` rigenerata), ma non sono i due termini del criterio 5/6.

## Output

Report: [[Report-Studio-OOS-Replica-Mensile-2026-07-01]].
Ledger e panel snapshot aggiornati (`experiments/replica_ledger/ledger.json`,
`data/snapshots/replica_panel/*.csv`), committati insieme al report.
