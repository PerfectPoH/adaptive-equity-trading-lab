---
tipo: methodology-ledger
progetto: adaptive-equity-trading-lab
data: 2026-05-17
status: SPEC_ONLY_NOT_EXECUTED
scope: multiple_testing_governance
---

# Report Methodology Gate Ledger - 2026-05-17

## Status

```text
SPEC ONLY / LEDGER BASELINE
NO NEW TRIAL OPENED
NO BACKTEST / NO OOS / NO SWEEP
```

This document establishes the baseline ledger for methodology governance before any future market-edge trial.

It is not a strategy report.

## Purpose

The project has accumulated multiple exploratory runs, fixes, ablations and pre-registered checks. Even when each step was documented, the sequence consumes degrees of freedom.

This ledger makes those degrees of freedom explicit and defines minimum gates before any new trial family can be opened.

## Standing prohibitions

```text
NO PAPER TRADING
NO PRODUCTION RANKING
NO DISCRETIONARY PARAMETER SWEEP
NO TRIAL-RANKEX-002
NO TRIAL-XMOM-001 UNTIL DATA + METHODOLOGY GATES PASS
NO SMALL-CAP TRIALS USING YFINANCE DAILY ALONE AS PRIMARY EVIDENCE
```

## Trial and research-family ledger

| Family | Items consumed | Current status | Promotion status | Notes |
|---|---|---|---|---|
| Infrastructure mechanics | risk-based sizing fix, cash ledger checks, artifact validator | active infrastructure | promoted as tooling only | Can be reused; not alpha evidence |
| Small-cap breakout/open-to-close | smoke runs, feature filters, temporal splits, EMA200 regime gate, corrected OOS/multi-year reruns | closed / archived | not promoted | Prior results reclassified as methodology/infrastructure stress tests |
| RankEx simple scanner-score ranking | `TRIAL-RANKEX-001`, ranking policy and validation | closed / failed validation | not promoted | Do not reuse `TRIAL-RANKEX-001`; do not open `TRIAL-RANKEX-002` as salvage |
| Data-quality gate | yfinance event audit spec/result, lessons learned | active blocking gate | not a strategy family | Verdict: `NOT_USABLE_FOR_SMALL_CAP_TRIALS_WITH_YFINANCE_DAILY_ALONE` |
| NCTRL negative control | scaffolding, property-check infrastructure, `TRIAL-NCTRL-001` | closed / technical pass | tooling only | Validates research machine, not alpha |
| Data provider evaluation | provider evaluation plan | spec-only / not executed | no provider selected | Necessary but not sufficient before small-cap reopening |
| Cross-sectional momentum vs IWM | candidate future direction | blocked | not opened | `TRIAL-XMOM-001` not authorized |
| Mean reversion / panic reversal | candidate future direction | parked | not opened | Requires separate preregistration and data/methodology gates |

## Consumed degrees of freedom

The following categories have already consumed research flexibility and must be counted when judging future evidence.

| Category | Examples already consumed | Consequence |
|---|---|---|
| Setup selection | breakout continuation, open-to-close filters, scanner setups | Cannot treat future nearby variants as first attempts |
| Threshold exploration | open_to_close thresholds around `0.08` and `0.10`, intraday range, relative volume, combined filters | Any future threshold must be predeclared or count as additional attempt |
| Regime gating | IWM EMA200 active/passive diagnostics | Regime gate cannot be retrofitted to rescue old families |
| Ranking policy | scanner-score RankEx and tie-breakers | Simple intra-candidate scanner ranking is closed |
| Window selection | 2024, H1/H2 2024, 2022-2024, H1/full 2025 | Future windows must be pre-registered |
| Outlier robustness | top1/top3 diagnostics repeatedly used | Ex-topN robustness remains mandatory |
| Benchmark design | random_entry_baseline, ticker_holding_window, IWM, equal-weight universe | Future benchmark set must include distribution-aware random baseline |
| Data-quality audit | event-selected yfinance audit | Current yfinance daily small-cap foundation is blocked |

## Minimum methodology gate before any new small-cap trial

A future small-cap trial may be drafted only after all of the following are true.

| Gate | Required status |
|---|---|
| Data provider evaluation | `provider_usable_for_small_cap_trials` or accepted caveated provider path |
| Point-in-time universe | explicit as-of construction and no survivor-only universe |
| Delisted/corporate actions | retrievable and auditable for adversarial event panel |
| Bootstrap random baseline | distribution-aware baseline with predeclared `N`, seed policy and percentiles |
| Artifact validation | target run must pass `run_artifact_validator` |
| Backtester audit | cash release, slippage, costs, EOP open-position handling and calendar handling audited |
| Multiple-testing ledger update | this ledger updated before preregistration |
| Trial accounting | `trial_id`, hypothesis family, windows, universe, decision rule and notes_on_multiple_testing predeclared |
| Ex-topN robustness | top1/top3 removal rule predeclared |
| Sample-size rule | closed-trade insufficiency rule predeclared |

## Trial opening protocol

Before opening a new trial ID:

1. update this ledger with the proposed family and related consumed attempts;
2. declare whether the proposal is genuinely new or adjacent to a closed family;
3. define train/design, validation and OOS windows;
4. freeze universe construction and data source;
5. declare benchmark set and random-baseline distribution policy;
6. declare outlier robustness and sample-size stop rules;
7. declare exact decision rule and stop conditions;
8. implement required infrastructure with TDD before execution;
9. run artifact validator after execution;
10. document verdict before any follow-up run.

## Naive multiple-testing policy

Until a formal Deflated Sharpe Ratio or equivalent framework exists, use this conservative rule:

```text
Each materially distinct strategy family starts with a maximum of one preregistered validation attempt.
Adjacent rescue variants after a failed family are presumed invalid unless justified as a new family before seeing results.
If a family has >= 3 exploratory variants or ablations, promotion thresholds must become stricter and ex-topN/random-distribution gates are mandatory.
If any validation fails its preregistered robustness gate, no OOS or paper trading is allowed for that trial.
```

This is intentionally conservative. It prevents “one more sweep” behavior.

## Blocked trial IDs and families

| Trial / family | Status | Reopen condition |
|---|---|---|
| `TRIAL-RANKEX-001` | closed / failed validation | never reuse; historical only |
| `TRIAL-RANKEX-002` | blocked | requires new hypothesis family, not scanner-score salvage |
| `TRIAL-XMOM-001` | blocked / not preregistered | data provider + methodology gate must pass first |
| archived breakout/open-to-close | closed / non-promotable | do not rescue with filters; infrastructure lessons only |
| yfinance-daily small-cap trial family | blocked | provider/data gate must pass; yfinance alone remains insufficient |

## Allowed next work

The following are allowed because they do not create new alpha evidence:

- execute the data provider evaluation plan;
- write a backtester audit plan/spec;
- harden artifact validation/report rebuild tooling;
- create a formal trial-accounting template;
- document a methodology gate without running it;
- evaluate non-small-cap methodology only with separate preregistration.

## Disallowed next work

The following remain disallowed:

- discretionary threshold sweeps;
- new small-cap backtests on current yfinance-daily foundation;
- OOS runs for failed validation trials;
- paper trading;
- production ranking;
- opening `TRIAL-XMOM-001` without provider + methodology gates;
- using NCTRL technical pass as alpha evidence.

## Ledger update requirement

Every future report that opens, closes or materially modifies a research family must update this ledger or explicitly state why no ledger update is needed.

A trial result is incomplete until the ledger reflects it.

## Decision

This ledger is now the baseline governance artifact for future methodology gates.

The project remains blocked from new small-cap strategy trials until data/provider and methodology gates pass and this ledger is updated before any run.


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
