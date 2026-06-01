# Public Catalyst PIT Audit Run 001

## Verdict

`PUBLIC_CATALYST_PIT_AUDIT_PARTIAL_NO_SOURCE_PROMOTABLE`

The audit found useful public and freemium discovery sources, but no observed free/public source passed the full point-in-time Catalyst sleeve contract by itself.

## What passed

Individual PDUFA dates can be timestamped from issuer press releases or SEC-linked exhibits. This means the lab can prove that some events were knowable before the event date.

Examples observed:

- Agios disclosed a September 7, 2025 PDUFA goal date in a January 8, 2025 company release.
- Liquidia disclosed a May 24, 2025 PDUFA goal date in a SEC-linked exhibit.

## What did not pass

No source observed in the tiny audit proved all of the following at once:

- complete historical event universe
- pre-event timestamp for every event
- failed, delayed, withdrawn, and missed event retention
- delisted/acquired sponsor retention
- stable machine export suitable for reproducible backtesting

## Source classes

Official sources such as FDA/openFDA and ClinicalTrials.gov are useful for verification and context, but they are not a clean historical PDUFA trading calendar.

Third-party sources such as BPIQ/BioPharmCatalyst, PDUFA.BIO, CatalystAlert, Dan Sfera, and BiotechEdge are useful discovery surfaces. Some look promising, especially sources that mention historical reports, CRLs, extensions, official-source links, or exports. They remain non-promotable until export, timestamping, and retention are audited.

## Practical conclusion

The free route is not dead, but it cannot be a single-source shortcut.

The only defensible public-data route is a hybrid construction:

1. Use a public/freemium calendar only to discover candidate events.
2. Require issuer PR, SEC filing, or archived page proof for the event date before the event.
3. Keep negative, delayed, withdrawn, and missed events explicitly.
4. Mark the panel non-promotable until coverage completeness is proven.

## Next valid action

Create a bounded `PUBLIC-CATALYST-HYBRID-EVENT-PANEL-GATE-001` that permits building a tiny non-promotable event panel from 10-20 events using only event-level timestamp proofs.

