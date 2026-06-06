# Candidate 010 Regime Strategy Map 001

Decision: `CANDIDATE_010_REGIME_STRATEGY_MAP_ARCHIVE_NO_PROMOTION`

Scope: fixed diagnostic atlas across predeclared strategy families and market regimes.
This is not a parameter search, not a portfolio optimizer, and not promotable from this dataset.

## Dataset

- Research symbols: `500`
- Active symbols: `250`
- Delisted symbols: `250`

## Overall Split Summary

- `is`: trades `118`, weighted net `-1.6273928601645338`, win rate `0.211864406779661`, max drawdown `-1.653608460511076`
- `oos`: trades `139`, weighted net `-0.8319837504599417`, win rate `0.31654676258992803`, max drawdown `-1.049828719082595`

## Top Descriptive OOS Cells

- `mean_reversion_5d` / `RISK_OFF`: trades `5`, weighted net `0.23665194831172287`, ex-top3 `0.03329133459664982`, passes cell gates `False`
- `momentum_60d` / `DRAWDOWN_STRESS`: trades `2`, weighted net `0.11562899906454628`, ex-top3 `0.0`, passes cell gates `False`
- `momentum_60d` / `TREND_UP_LOW_VOL`: trades `15`, weighted net `0.054821742351505755`, ex-top3 `-0.08435469053277714`, passes cell gates `False`
- `momentum_60d` / `RECOVERY_BOUNCE`: trades `8`, weighted net `0.05314854729110688`, ex-top3 `-0.09992166683238879`, passes cell gates `False`
- `mean_reversion_5d` / `DRAWDOWN_STRESS`: trades `5`, weighted net `0.019019255501547223`, ex-top3 `-0.04156329546160054`, passes cell gates `False`
- `momentum_60d` / `RISK_OFF`: trades `2`, weighted net `0.0069393276179451294`, ex-top3 `0.0`, passes cell gates `False`
- `mean_reversion_5d` / `RECOVERY_BOUNCE`: trades `8`, weighted net `-0.012319383457483082`, ex-top3 `-0.08057300846608761`, passes cell gates `False`
- `volatility_compression_20d` / `TREND_UP_HIGH_VOL`: trades `2`, weighted net `-0.0187071097183303`, ex-top3 `0.0`, passes cell gates `False`
- `volatility_compression_20d` / `RISK_OFF`: trades `2`, weighted net `-0.019419841799308543`, ex-top3 `0.0`, passes cell gates `False`
- `dollar_volume_shock_20d` / `RISK_OFF`: trades `3`, weighted net `-0.03143997849633753`, ex-top3 `0.0`, passes cell gates `False`

## Blockers

- `diagnostic_only_regime_atlas`
- `same_dataset_as_prior_candidates`
- `trial_limited_two_year_history`
- `descriptive_ranking_not_promotable`
