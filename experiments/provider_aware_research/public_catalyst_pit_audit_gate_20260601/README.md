# Public Catalyst PIT Audit Gate 001

This gate defines the audit required before any public or freemium biotech/PDUFA source can feed the Catalyst sleeve of Portfolio Candidate 002.

No scraping, provider query, market-data download, backtest, paper trading, or promotion is authorized by this gate.

## Core problem

Public biotech catalyst calendars can be useful for discovery, but they are dangerous for backtesting unless the lab can prove point-in-time availability and negative-event retention.

A calendar that shows only currently known future catalysts or only successful/remembered events creates look-ahead bias, survivorship bias, and outcome-selection bias.

## Minimum admissibility contract

A source must provide or allow reconstruction of:

- event date
- event type
- company/ticker mapping
- drug or asset name
- indication
- source timestamp or archived proof that the date was known before the event
- outcome-retention policy, including failed, delayed, withdrawn, and missed events
- delisted/acquired company retention policy
- machine-readable or reproducibly scrapeable access path

## Candidate interpretation

FDA/openFDA and ClinicalTrials.gov are official and free. They are useful for post-event verification, trial metadata, and approval records, but they do not by themselves provide a clean historical point-in-time PDUFA trading calendar.

Public PDUFA calendars are useful discovery surfaces. They remain non-promotable until the source proves archiveability, timestamping, and complete retention of negative outcomes.

