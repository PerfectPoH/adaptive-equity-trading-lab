# Report SEC8K Predrift Existing Daily Diagnostic - 2026-05-23

Decision: `SEC8K_PREDRIFT_ARCHIVE_CURRENT_FORM`

## Scope

Existing daily artifacts only. No provider query, market-data download, intraday query, parameter sweep, backtest, paper/live trading, or promotion occurred.

## Result

- Event count: 87
- Control count: 4798
- Event median pre-window return: -0.0163793103
- Control median pre-window return: -0.0051319675
- Signed return lift: -0.0112473428
- Event median pre-window abs return: 0.076142132
- Control median pre-window abs return: 0.0636257243
- Abs return lift: 0.0125164077
- Event median pre-window volume ratio: 1.11705279
- Control median pre-window volume ratio: 0.98159957
- Volume ratio lift: 0.13545322
- Blockers: event_signed_predrift_not_above_control

## Interpretation

This diagnostic tests whether SEC 8-K Item 2.02 events are preceded by measurable daily drift. It is not a trading strategy and cannot promote without a separate trial.
