# Candidate 013 Probe 001 Corrective Report

Probe 001 is archived as an implementation-signature error, not as a provider entitlement verdict.

The historical metadata portion completed, but the Reference API checks passed an unsupported `limit` keyword to `get_range`. Databento's Reference endpoints use bounded `start`, `end`, and `symbols` arguments instead. Because the Reference calls failed locally with `TypeError`, Probe 001 cannot answer whether Reference entitlement is available.

Correction: create a separate rerun gate before the corrected probe is executed. The rerun remains bounded, retains no raw provider payload, performs no market-data download, and authorizes no backtest or promotion.
