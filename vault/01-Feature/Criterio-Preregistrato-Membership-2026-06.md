---
tipo: criterio-preregistrato
progetto: adaptive-equity-trading-lab
data: 2026-06-11
stato: congelato-prima-del-primo-report-mensile
ultimo-aggiornamento: 2026-06-11
tags: [preregistrazione, membership, replica, criterio-successo]
---

# Criterio preregistrato - Ipotesi Membership (congelato 2026-06-11)

> Scritto PRIMA del primo report mensile, su proposta dell'audit esterno.
> Qualsiasi modifica dopo il primo report invalida il criterio.

## Ipotesi sotto test

La MEMBERSHIP del regime router (quali componenti ammette per regime,
blend statico, MAI switching) aggiunge valore rispetto alla selezione
semplice. Valore osservato in-program: +32.7pp
([[Report-Honest-Baselines-Trial-2026-06-11]], addendum).

ATTENZIONE ANCORAGGIO: +41.1% / +32.7pp sono misurati sullo stesso OOS 2025
guardato decine di volte, su pool curato col senno di poi. E' l'ipotesi piu'
probabile del programma, NON un risultato. Questo criterio esiste per
impedire che diventi la nuova ancora come lo fu il +49.6%.

## Nota definitoria (da non ricostruire tra sei mesi)

`membership_blend_static` pesa i regimi in modo UGUALE, a prescindere dalla
loro frequenza storica: e' la scelta a zero informazione di timing. Pesare
per frequenza storica introdurrebbe timing implicito.

## Criterio di successo (6 mesi)

Su 6 report mensili consecutivi del companion gate (honest_baselines_trial):

1. `membership_blend_static - unconditional_top5 > 0` in ALMENO 5 su 6;
2. delta cumulato sui 6 mesi POSITIVO;
3. DSR della serie membership alla multiplicita' di FAMIGLIA dal
   program_trial_counter (non a costanti dichiarate).

Esito PASS: si apre la decisione data bundle - comprare dati per testare
un'ipotesi sopravvissuta a dati mai visti, non per cercarne una nuova.
Esito FAIL: ipotesi membership archiviata; il lab resta infrastruttura +
replica, senza nuovi acquisti dati.

## PREREQUISITO BLOCCANTE (scoperto alla stesura)

Gli stream dei componenti vengono da artifact salvati e price file fermi al
2026-05-08: SENZA refresh dei dati ogni replica mensile produrrebbe risultati
IDENTICI e il criterio passerebbe per costruzione. Prima del primo report
(2026-07-01) serve RISK-044: estensione causale degli stream con dati freschi
(refresh del price panel + rigenerazione deterministica delle entry SOLO sui
nuovi mesi, senza ricalcolare le soglie sul passato). Finche' RISK-044 e'
aperto, i report mensili contano come VERIFICA DI RIPRODUCIBILITA', non come
evidenza nuova, e il conteggio dei 6 mesi NON parte.

Vedi [[Stato-Corrente]], [[Report-External-Audit-2026-06-11]].

---

## Emendamento 001 (2026-06-11, stesso giorno, PRIMA del primo report mensile)

RISK-044 implementato e validato end-to-end (`stream_extension.py`,
flag `--extend-streams` nel companion gate). Coverage del primo run:
32 componenti estesi, 195 trade nuovi chiusi, 270 pendenti, 76 congelati
(template non causale o eventi: restano onestamente fermi).

Precisazioni operative scoperte alla validazione:

1. **Regola di conteggio mesi**: un mese CONTA per il criterio 5/6 solo se
   `membership_blend_static` O `unconditional_top5` cambiano rispetto al mese
   precedente (= almeno un trade chiuso e' entrato nei loro stream). I mesi
   senza variazione non contano ne' a favore ne' contro. Motivo: i basket
   member principali hanno holding 90/180d - i loro primi trade post-freeze
   chiudono ~settembre 2026 (90d) e ~febbraio 2027 (180d).
2. **Regime map forward-fill**: le label di regime per i periodi nuovi sono
   il forward-fill dell'ultima label nota (2026-05-08). Limite dichiarato;
   un refresh causale della regime map e' lavoro futuro separato.
3. I trade pendenti vengono tracciati (`pending_open_trades`) e compaiono
   nei report mensili come "pipeline in maturazione".

---

## Emendamento 002 (2026-06-11, audit round 3, PRIMA del primo report mensile)

1. **Regola delisting (chiude il survivorship nei dati freschi)**: un simbolo
   che sparisce produce SEMPRE un'uscita realizzata, mai un trade svanito.
   Panel "stale" (ultimo dato >7 giorni indietro rispetto al resto): i trade
   aperti chiudono all'ULTIMO CLOSE disponibile (`delisted_last_close`).
   Simbolo sparito del tutto: chiusura a -100% (`symbol_vanished_total_loss`).
2. **Entry ledger persistente** (`experiments/replica_ledger/ledger.json`,
   tracciato in git): le entry si persistono alla prima rilevazione (data,
   simbolo, prezzo); i run successivi maturano SOLO le uscite dal ledger e
   non rigenerano mai entry passate - immune al re-aggiustamento retroattivo
   di yfinance. Se il ricalcolo odierno non conferma un'entry del ledger:
   `data_revision_warnings` nel coverage (rivelatore di revisioni fonte).
3. **Seam check eseguito** (finestra overlap 2026-01-02 -> 2026-05-08):
   overlap_ratio = 0.573 (248/433 entry congelate ritrovate dalle regole
   causali su yfinance). Coerente con l'Emendamento 001 (regole causali !=
   ranking ex-post congelato). LETTURA OBBLIGATORIA nei report: l'evidenza
   mensile misura la VARIANTE CAUSALE della membership, non la continuazione
   perfetta degli stream storici - e' l'unica variante implementabile.
   Artifact: `experiments/runs/seam_check_20260611_213905/`.
4. **Regime history refresh**: il classifier causale rigenera
   `regime_history` dal panel SPY fresco a ogni replica
   (`replica_support_checks`), cosi' la diagnostica timing resta viva.
   La gamba membership non dipende dalle label OOS (blend statico).

---

## Emendamento 003 (2026-06-11, audit round 4, PRIMA del primo report mensile)

Un download fallito NON e' un delisting. Senza questa regola, un singolo
rate-limit di Yahoo avrebbe scolpito -100% falsi e PERMANENTI nel ledger
immutabile.

1. **Retry + pausa**: `refresh_panel` ritenta il download (3 tentativi,
   backoff) e attende 0.4s tra simboli, come il downloader MVP.
2. **Cache fallback**: download vuoto con cache CSV esistente (di qualunque
   eta') -> si usa la cache con status `stale`: i pendenti chiudono
   all'ultimo close. Per un delisting vero e' anche piu' accurato del -100%.
3. **Quarantena a doppia conferma**: `no_data` senza alcuna cache -> il trade
   resta `open` con marker `suspect_vanished`; la chiusura a -100% scatta
   SOLO se `no_data` viene confermato anche al run successivo. Se il simbolo
   torna, la quarantena si pulisce e la maturazione e' normale.
4. **Maturazione sotto revisione dati**: se la data di entry non esiste piu'
   nella fonte, si matura dalla prima barra >= entry date (prezzo di entry
   sempre dal ledger) con flag `data_revision` - nessuna entry resta open
   per sempre quando il panel copre entry+holding.

Distribuzione attesa degli esiti: `delisted_last_close` come via normale,
`symbol_vanished_total_loss` come eccezione documentata (simbolo mai
scaricato con successo, confermato due volte). Coverage: nuovo campo
`suspect_vanished_quarantine` nei report mensili.

Validazione: 5/5 test (quarantena, ritorno dalla quarantena, revisione dati,
ledger idempotente, stale); run reale idempotente sul ledger esistente.
