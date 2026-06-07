# Candidate 018 FMP Micro-Probe 001 Endpoint Family Correction

The run respected the pre-run gate and did not retain raw payloads, build a dataset, run a backtest, or promote a strategy.

During review, the first FMP probe was found to use legacy `/api/v3` endpoint paths. Current FMP documentation identifies `/stable/` as the API base for the newly issued API-key flow.

Run 001 remains archived as a blocked legacy-endpoint probe. It must not be used as final evidence about FMP admissibility until a separate pre-run gate authorizes a `/stable/` endpoint rerun.
