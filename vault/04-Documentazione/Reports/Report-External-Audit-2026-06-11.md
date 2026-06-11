---
tipo: report
progetto: adaptive-equity-trading-lab
data: 2026-06-11
fonte: audit-esterno-fornito-dall-owner
ultimo-aggiornamento: 2026-06-11
tags: [audit, backtest, overfitting, p-hacking, motore, metodologia]
---

# Report - Audit Esterno Motore e Metodologia (2026-06-11)

> Audit indipendente fornito dall'owner in chat. Claim B1 (cost-tier artifact)
> e B2 (12 duplicati) VERIFICATI numericamente dal lab lo stesso giorno:
> tier {100:26, 200:1, 350:1, 375:14, 500:66}, medie OOS per fascia
> {100: +8.27, 375: -3.49, 500: -1.97}, 12 duplicati su 108. Esatti.
> Risposta operativa: [[Report-Honest-Baselines-Trial-2026-06-11]].
> Vedi [[Stato-Corrente]] e [[Memoria-AI]].

## Sintesi dell'audit (testo integrale conservato dall'owner in chat)

Verdetto sintetico: il motore non bara intenzionalmente; cultura metodologica sopra la media. Ma: (B1) il gate BEATS_STATIC e' vinto in gran parte da un artefatto dei cost tier (~76% del pool cost-crippled; static onesta a <=100bps = +29.2% vs -22.9% usata nel gate; delta routing reale ~+20pp, non +72.5pp). (B2) 12 stream duplicati contaminano baseline, correlazioni e sharpe_std del DSR. (B3) multiplicita' reale di programma >> trial_count=2 dichiarato; dsr_by_trial_count mostra che il risultato non regge oltre ~3-5 look. (B4) selection bias della libreria componenti (curata conoscendo il 2024-25). (B5) entry_bar_exit_touch nel MVP e' un look-ahead documentato ma da correggere. (B6-B8) sizing su equity fissa, benchmark senza dividendi, off-by-one timeout, f-string non portabile, embargo_days=0 default.

Suggerimenti chiave: baseline a parita' di costi + dedup + PERMUTATION TEST delle label di regime (unico test che dimostra skill di routing); trial counter automatico collegato a effective_trial_count; fix entry_bar_exit_touch e rerun MVP; promuovere true_etf_backtest a motore unico; replica mensile con criterio di successo definito PRIMA; TRUE-ETF-003 con ~50 ETF prima di comprare dati small-cap; "ETF semplici + risk overlay classifier" come candidato a multiplicita' 1.
