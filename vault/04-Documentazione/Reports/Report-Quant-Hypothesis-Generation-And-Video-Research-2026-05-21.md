# Report Quant Hypothesis Generation And Video Research - 2026-05-21

## Status

`RESEARCH_NOTES_ARCHIVED_SPEC_ONLY`

This report archives the research notes gathered after the first bounded XMOM earnings provider probe.

It is not a preregistration, not an executable strategy spec, and not permission to run provider queries, OOS tests, paper trading, or live trading.

## Context

The lab has already reached a useful state:

- XMOM-001 was executed and rejected for outlier dependence.
- Catalyst forensics showed that small-cap momentum was acting as a blind proxy for event exposure.
- The implementation-gate stack now includes CPCV, PSR/DSR, effective trial count and a synthetic statistical gate harness.
- The first Intrinio earnings single-probe was executed once and returned `HTTP_ERROR_403 / Forbidden`, so earnings timestamp data remains a provider-access blocker.

The next useful work is therefore not "find a magic strategy", but define falsifiable hypotheses that can later pass through the existing governance gates.

## Research Principle

The lab should treat strategies as hypotheses, not products.

```text
Hypothesis -> preregistration -> data contract -> validation gate -> one execution -> falsification or survival.
```

Useful alpha candidates are not copied from videos, forums, or papers. They are translated into narrow, testable propositions with explicit kill conditions.

## Vector 1 - PEAD, Illiquidity And Small-Cap Quality

### Idea

Post-Earnings Announcement Drift (PEAD) is a persistent anomaly where stocks continue drifting in the direction of an earnings surprise after the announcement.

The research notes emphasize that PEAD is strongest where arbitrage is hardest:

- lower liquidity;
- wider spreads;
- lower analyst coverage;
- higher idiosyncratic volatility;
- higher execution friction.

This means PEAD cannot be evaluated gross of costs. If execution costs consume most of the anomaly, a beautiful backtest is not useful.

### Useful Lab Translation

Future PEAD trials must combine:

- earnings timestamp quality: only clean BMO/AMC events;
- earnings surprise proxy or documented catalyst class;
- Amihud illiquidity or a related liquidity-risk measure;
- quality filter for small caps, avoiding pure junk exposure;
- execution-cost stress;
- DSR/PSR after trial accounting.

### Falsification Conditions

Reject the hypothesis if:

- timestamp coverage is too poor;
- post-cost returns vanish;
- performance comes from a few outliers;
- small-cap quality filter is non-operational;
- DSR fails after effective trial count correction.

## Vector 2 - Binary Biotech Catalysts

### Idea

Biotech and healthcare small caps are dominated by discrete binary events:

- FDA decisions;
- PDUFA dates;
- clinical trial readouts;
- advisory committee events;
- single-asset pipeline shocks.

These events are not normal momentum. They are discontinuous repricing events with asymmetric payoff profiles.

### Useful Lab Translation

This belongs in a separate event-driven research track, not as a patch to XMOM-001.

Required before any real test:

- deterministic event calendar;
- event type taxonomy;
- BMO/AMC/DMT/UNSPECIFIED timestamp mapping;
- explicit exclusion of ambiguous intraday or date-only events;
- pre-event drift window definition;
- no holding through binary release unless the hypothesis is specifically designed for binary risk.

### Falsification Conditions

Reject the hypothesis if:

- event timestamps are missing or too ambiguous;
- DMT/UNSPECIFIED purge rate breaches the threshold;
- losses are dominated by binary release exposure;
- wins require unknowable ex-ante outcomes;
- result survives only because of one or two extreme positive events.

## Vector 3 - Intraday Gap-Down Reversion

### Idea

Extreme overnight gap-downs may overreact at the open and partially mean-revert intraday once forced selling is absorbed.

The tentative hypothesis:

```text
Long-only gap-down reversion may work when a stock opens down hard,
shows abnormal volume, reclaims VWAP before late morning,
and trades inside a supportive macro regime.
```

### Candidate Features

Possible future spec-only variables:

- overnight gap magnitude;
- relative opening volume;
- first-30-minute volume shock;
- VWAP reclaim by a fixed time such as 10:30 New York;
- macro regime filter;
- Amihud/liquidity capacity filter;
- no-trade filter for known catastrophic breakaway events.

### Important Warning

This is the most immediately testable idea, but also the easiest to overfit.

It must not start as a parameter sweep over gap thresholds, reclaim times and holding periods. It must start as a preregistered hypothesis with a tiny set of fixed parameters or a blind distributional selection process.

### Falsification Conditions

Reject the hypothesis if:

- winners depend on a few extreme reversals;
- transaction costs or spread assumptions remove the edge;
- VWAP reclaim timing is selected from in-sample PnL;
- intraday data quality is insufficient;
- DSR fails after trial accounting.

## Video Notes

### 1. Jim Simons / Renaissance Technologies

Useful ideas:

- focus on stable statistical structure, not market stories;
- search for many small edges rather than one heroic signal;
- treat the infrastructure itself as an alpha factory;
- consider future meta-labeling and regime switching;
- use alternative data only after governance exists.

Lab translation:

- keep feature discovery blind-to-returns where possible;
- never promote a story without statistical survival;
- treat model context selection as a future meta-layer, not a patch to failed trials.

### 2. Umar Ashraf / 15 Unprofitable Traders

Useful ideas:

- most discretionary failure is a control-system failure;
- revenge trading, PnL fixation and rule-breaking can be converted into software constraints;
- a winning trade that violated the protocol is not a good trade.

Lab translation:

- future live/paper execution should support blind PnL mode;
- trade logs should classify `GOOD_WIN`, `GOOD_LOSS`, `BAD_WIN`, `BAD_LOSS`;
- strategy metrics should be recomputed excluding or penalizing `BAD_WIN`;
- stop-loss events should trigger ticker-level cooldown locks.

These are live-execution guardrails, not current research priorities.

### 3. Advanced Charts / Footprint / Liquidity Heatmaps

Useful ideas:

- OHLCV candles hide order-flow structure;
- time bars overweight quiet periods and underrepresent active periods;
- dollar bars or volume bars may stabilize statistical sampling;
- footprint/order-flow data can identify absorption;
- L2/L3 order-book data can identify liquidity walls or adverse book conditions.

Lab translation:

- future data architecture should consider volume bars and dollar bars;
- gap-down reversion could later add an absorption filter;
- LOB/heatmap logic is an advanced data-engineering track, not an immediate Python MVP task.

## Future Research Backlog

These ideas are useful, but none are executable yet.

### Near-Term Spec Candidates

- `TRIAL-GAPREV-001`: long-only intraday gap-down reversion, preregistered and intraday-data dependent.
- `TRIAL-PEAD-QUALITY-001`: PEAD with timestamp-quality, liquidity and small-cap quality constraints.
- `TRIAL-BIOTECH-CATALYST-001`: binary catalyst event study, separate from earnings.

### Long-Term Architecture Candidates

- volume-bar and dollar-bar builder;
- meta-labeling layer for position sizing;
- trade-quality taxonomy for live/paper logs;
- order-flow absorption detector;
- L2/L3 order-book pre-trade filter;
- blind PnL execution UI;
- ticker-level cooldown lock after stop-loss.

## Governance Position

Current allowed action:

```text
archive research notes
write spec-only docs
design future preregistration gates
```

Current blocked action:

```text
provider query loops
endpoint guessing
extractor implementation
parameter sweeps
OOS execution
paper trading
live trading
strategy promotion
```

## Decision

The notes are valuable and should remain in the vault as a directional map for future hypothesis generation.

They do not override the current provider-access blocker from the Intrinio `HTTP_ERROR_403`, and they do not authorize any new data pull.


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
