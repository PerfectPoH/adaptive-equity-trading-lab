# Report SEC 8-K Multisymbol Event Timing Diagnostic - 2026-05-22

Decision: `SEC_8K_MULTISYMBOL_TIMING_CANDIDATE_ONLY`

## Scope

Bounded multi-symbol SEC EDGAR Item 2.02 timing diagnostic on symbols already present in the XMOM Databento price panel. SEC submissions were queried for event timestamps; no raw SEC payload was retained. Existing Databento prices were reused. No market-data download, strategy backtest, parameter sweep, paper/live trading or promotion was performed.

## Result

- Symbols: AEHR, ARRY, CABA, CRMD, IOVA
- Event days covered by prices: 87
- Control days: 4823
- Event median absolute return: 0.0724637681
- Control median absolute return: 0.0299477103
- Absolute-return lift: 0.0425160578
- Event median volume ratio: 3.03102063
- Control median volume ratio: 0.98366013
- Volume-ratio lift: 2.0473605
- Blockers: candidate_requires_separate_preregistration_and_direction_source

## Events By Symbol

- AEHR: 34
- ARRY: 24
- CABA: 29
- CRMD: 49
- IOVA: 47

## Interpretation

This diagnostic tests whether SEC 8-K Item 2.02 acceptance timing marks high-volatility/high-volume regimes across multiple issuers. It does not infer earnings surprise or tradable direction from future returns.


Vedi [[Documentazione-Index]] e [[Stato-Corrente]].
