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
