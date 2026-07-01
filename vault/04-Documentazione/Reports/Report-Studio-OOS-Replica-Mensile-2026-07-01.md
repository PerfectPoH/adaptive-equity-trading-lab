---
tipo: report
progetto: adaptive-equity-trading-lab
data: 2026-07-01
trial: TRIAL-STUDIO-OOS-REPLICA
ultimo-aggiornamento: 2026-07-01
tags: [oos, replica-mensile, membership, timing, dsr, ledger, scheduled]
---

# Report - Replica Mensile OOS Congelato (2026-07-01)

Decision: `OOS_POSITIVE__BEATS_STATIC__OUTLIER_ROBUST__DSR_PASS` (replica)
/ `ROUTING_SKILL_NOT_CONFIRMED__S3` (companion gate)

Replica #1 del protocollo congelato in [[Criterio-Preregistrato-Membership-2026-06]]
(congelato 2026-06-11). Nessuna modifica a codice, parametri, criterio o ledger a mano.

## Stato conteggio mesi: 1 di 6 - NON CONTATO

Regola (Emendamento 001): un mese conta per il criterio 5/6 solo se
`membership_blend_static` O `unconditional_top5` cambiano rispetto al mese
precedente. Questo mese:

- `membership_blend_static`: 0.4113 -> 0.4113 (**invariato, bit-identico**)
- `unconditional_top5`: 0.083574 -> 0.083574 (**invariato, bit-identico**)

**Mese non contato (stream membership invariati; pendenti: 260).** Esito
atteso e previsto testualmente dall'Emendamento 001: i basket member
principali hanno holding 90/180d, i primi trade post-freeze (2026-06-11)
chiudono ~settembre 2026 (90d) e ~febbraio 2027 (180d). A meno di 20 giorni
dal freeze non c'era alcuna possibilita' che questi due stream si muovessero,
ed e' esattamente quello che si osserva: valori identici al bit rispetto al
run di freeze (`experiments/runs/honest_baselines_008_20260611_214711/result.json`).
Conteggio 5/6: **0 mesi contati finora**.

## Verdetti

| Componente | Verdetto |
|---|---|
| Replica protocollo congelato (`studio_oos_runner`, cutoff 2025-01-01, vol-norm, rule, top-5) | `OOS_POSITIVE__BEATS_STATIC__OUTLIER_ROBUST__DSR_PASS` |
| Companion gate (`honest_baselines_trial --extend-streams`) | `ROUTING_SKILL_NOT_CONFIRMED__S3` |
| Gate S1 (batte static cost-matched) | PASS |
| Gate S2 (batte unconditional top-5) | PASS |
| Gate S3 (permutation timing) | FAIL (n.s.) |
| `promotion_allowed` | false — nessuna promozione (invariato) |

Artifact: `experiments/runs/studio_oos_replica_20260701_192013/`,
`experiments/runs/honest_baselines_008_20260701_192120/`,
`experiments/runs/seam_check_20260701_191926/`,
`experiments/runs/regime_index_refresh_20260701/`.

## Confronto vs riferimenti al freeze (2026-06-11)

| Metrica | Freeze (2026-06-11) | Questo mese (2026-07-01) | Delta |
|---|---|---|---|
| `dynamic_regime_routed` | +49.6% | +49.63% | **invariato** (bit-identico: 0.496308) |
| `static_cost_matched` | +27.8% | +24.88% | -2.90pp |
| `static_all_legacy` | -26.3% | -29.11% | -2.85pp |
| `unconditional_top5` | +8.4% | +8.36% | **invariato** (bit-identico) |
| `membership_blend_static` | +41.1% | +41.13% | **invariato** (bit-identico) |
| p-value (permutation, S3) | 0.1393 | 0.1443 | +0.0050 |

`dynamic_regime_routed` e' la regola preregistrata congelata su cutoff
2025-01-01: riproducibilita' esatta attesa e osservata. `static_cost_matched`
e `static_all_legacy` SI muovono perche' dipendono da stream con holding piu'
corti che maturano gia' in un mese — sono diagnostici del companion gate, non
i due termini del criterio 5/6. Il p-value oscilla perche' `regime_history` e'
rigenerato da zero ad ogni run dal panel SPY fresco (Emendamento 002 punto 4);
questa e' diagnostica di timing, non ha impatto sulla gamba membership.

## Coverage ledger (entry ledger persistente)

| Campo | Freeze (195 chiusi / 270 pendenti) | Questo mese |
|---|---|---|
| `new_trades_closed` | 195 | **393** |
| `pending_open_trades` | 270 | **260** |
| `delisting_closures` | 0 | 0 |
| `suspect_vanished_quarantine` | 0 | 0 |
| `data_revision_warnings` | 0 | **9** |
| `extendable` / `frozen` (template non causale) | 32 / 76 | 32 / 76 |

Nota sui campi (promemoria dal task): `new_trades_closed` / `pending_open_trades`
= pipeline in maturazione; `delisting_closures` = uscite REALIZZATE per
delisting, esito normale del protocollo, non un'anomalia (questo mese: 0);
`suspect_vanished_quarantine` = simboli in quarantena a prima conferma
`no_data` (nessuna perdita registrata finche' non arriva la seconda conferma;
questo mese: 0, nessun simbolo in quarantena).

**In evidenza — `data_revision_warnings` = 9 (era 0 al freeze).** yfinance ha
riscritto la storia per 9 entry del ledger rispetto a quanto registrato alla
prima rilevazione: il ricalcolo odierno non ha confermato la entry originale
a quella data/prezzo. Per la regola dell'Emendamento 003 punto 4, queste
entry maturano comunque dalla prima barra disponibile >= entry date (prezzo
di entry sempre dal ledger, mai riscritto), con flag `data_revision` — nessun
impatto sulla decisione di questo mese, ma la fonte va tenuta d'occhio: se il
conteggio cresce mese su mese potrebbe indicare instabilita' strutturale
della serie storica free-tier, non un evento isolato.

Seam check ripetuto in `replica_support_checks`: overlap_ratio = 0.573
(248/433, 32 componenti) — identico al check originale
(Emendamento 002 punto 3), riproducibilita' confermata sulla finestra
2026-01-02 -> 2026-05-08.

## Ipotesi (a): MEMBERSHIP — variante causale, seam 0.573

`membership_blend_static - unconditional_top5`:

- Delta di questo mese: 0.4113 - 0.083574 = **+32.77pp** (freeze: +32.7pp,
  invariato perche' entrambi i termini sono invariati).
- Delta cumulato sui mesi CONTATI: **N/A — 0 mesi contati finora** (questo
  mese non entra nel conteggio 5/6 ne' nel cumulato, per costruzione: e' lo
  stesso dato del freeze, non nuova evidenza).
- Lettura obbligatoria (Emendamento 002 punto 3): questa evidenza misura la
  VARIANTE CAUSALE della membership (regole causali su yfinance, seam
  overlap 0.573 con il ranking ex-post congelato), non la continuazione
  perfetta degli stream storici — e' l'unica variante implementabile e resta
  coerente con l'osservazione in-program (+32.7pp).

## Ipotesi (b): TIMING — diagnostica p-value/regime, non sommare a (a)

- `timing_delta_vs_membership`: +8.50pp (freeze: +8.50pp, invariato — dipende
  da `dynamic_regime_routed` e `membership_blend_static`, entrambi invariati
  questo mese).
- p-value permutation: 0.1443 (freeze: 0.1393), n.s. a soglia 0.05. Oscilla
  per il refresh di `regime_history`, non per un cambiamento della membership.
- Gate S3 resta FAIL: il timing di regime non e' statisticamente dimostrato
  su questo campione, invariato rispetto al freeze.

Le due ipotesi NON si sommano: +32.77pp (membership) e +8.50pp (timing) sono
letture separate sullo stesso decompose, non un totale unico.

## Governance

Nessuna promozione. Nessuna provider query oltre al refresh yfinance
autorizzato dal protocollo. Nessuna modifica a codice, parametri, criterio o
ledger a mano — solo esecuzione dei tre runner e lettura degli output.
RISK-044 chiuso, conteggio 6 mesi attivo dal 2026-07-01 (questo report è il
mese 1, non contato).

## Riferimenti

[[Criterio-Preregistrato-Membership-2026-06]] · [[Report-Honest-Baselines-Trial-2026-06-11]]
· [[Report-External-Audit-2026-06-11]] · [[Report-Studio-OOS-Validation-2026-06-11]]
