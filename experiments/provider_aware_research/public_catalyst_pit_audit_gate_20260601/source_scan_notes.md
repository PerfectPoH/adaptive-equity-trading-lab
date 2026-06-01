# Source Scan Notes

Public catalyst research splits into two different jobs:

1. **Verification sources**: FDA/openFDA, ClinicalTrials.gov, SEC EDGAR, and company releases can verify that an event happened or that a company disclosed a date.
2. **Tradable calendar sources**: a PDUFA/catalyst calendar must prove what was knowable before the event, not merely what is visible after the event.

The audit therefore starts with a very small manual sample. The lab should not scrape bulk calendars until a source proves it can pass the point-in-time checks.

## Important caveat

The FDA does not provide a clean official public master list of all future PDUFA dates suitable for historical trading simulation. Public calendars generally aggregate company disclosures, FDA context, and manual curation. That makes them useful, but not automatically admissible.

