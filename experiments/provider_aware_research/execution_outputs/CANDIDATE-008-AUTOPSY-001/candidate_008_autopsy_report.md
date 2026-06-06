# Candidate 008 Autopsy 001

Decision: `CANDIDATE_008_AUTOPSY_COMPLETE_NO_BACKTEST`

Scope: read-only attribution. No provider query, no new backtest, no promotion.

## Sleeve Attribution

- `mean_reversion_5d`: trades `95`, weighted net `-0.3202726788469614`, win rate `0.3684210526315789`
- `momentum_60d`: trades `62`, weighted net `-0.20200315908292613`, win rate `0.3870967741935484`

## Universe Attribution

- `active`: trades `99`, weighted net `-0.27547208125458766`, win rate `0.42424242424242425`
- `delisted`: trades `58`, weighted net `-0.2468037566752998`, win rate `0.29310344827586204`

## Cost Drag

- Gross weighted sum: `0.2627241620701103`
- Weighted cost sum: `0.7850000000000003`
- Weighted net sum: `-0.5222758379298875`

## Recommendations

- `sleeve:mean_reversion_5d`: Do not route capital to this sleeve without a separate preregistered regime filter.
- `sleeve:momentum_60d`: Do not route capital to this sleeve without a separate preregistered regime filter.
- `universe:active`: Inspect whether tradability or delisting timing requires a stricter as-of filter.
- `universe:delisted`: Inspect whether tradability or delisting timing requires a stricter as-of filter.
- `cost_drag`: Any next hypothesis must justify maker/limit execution or larger gross moves before backtesting.
