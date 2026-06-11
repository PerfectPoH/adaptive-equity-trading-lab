# Report Dollar-Bar Diagnostic - 2026-05-21

Decision: `DOLLAR_BAR_DIAGNOSTIC_COMPLETE_NO_STRATEGY`

## Scope

Diagnostic-only transformation of existing Databento intraday bar artifacts into dollar bars. No provider query, strategy backtest, paper/live trading or promotion was performed.

## Result

- Evaluated files: 12
- Improved distributions: 11
- Median stability score delta: 19.806168

## Panel

- AEHR bars=751 dollar_bars=310 delta=163.000176 verdict=DOLLAR_BARS_DISTRIBUTION_IMPROVED_DIAGNOSTIC_ONLY
- AEHR bars=702 dollar_bars=263 delta=25.347831 verdict=DOLLAR_BARS_DISTRIBUTION_IMPROVED_DIAGNOSTIC_ONLY
- ARRY bars=742 dollar_bars=305 delta=201.256092 verdict=DOLLAR_BARS_DISTRIBUTION_IMPROVED_DIAGNOSTIC_ONLY
- CABA bars=124 dollar_bars=34 delta=5.300252 verdict=DOLLAR_BARS_DISTRIBUTION_IMPROVED_DIAGNOSTIC_ONLY
- CABA bars=230 dollar_bars=86 delta=-0.833072 verdict=DOLLAR_BARS_NO_STABILITY_IMPROVEMENT
- CABA bars=131 dollar_bars=42 delta=3.6146 verdict=DOLLAR_BARS_DISTRIBUTION_IMPROVED_DIAGNOSTIC_ONLY
- CABA bars=185 dollar_bars=67 delta=14.264505 verdict=DOLLAR_BARS_DISTRIBUTION_IMPROVED_DIAGNOSTIC_ONLY
- CABA bars=651 dollar_bars=209 delta=121.111407 verdict=DOLLAR_BARS_DISTRIBUTION_IMPROVED_DIAGNOSTIC_ONLY
- CABA bars=442 dollar_bars=146 delta=6.151396 verdict=DOLLAR_BARS_DISTRIBUTION_IMPROVED_DIAGNOSTIC_ONLY
- CRMD bars=439 dollar_bars=142 delta=10.414652 verdict=DOLLAR_BARS_DISTRIBUTION_IMPROVED_DIAGNOSTIC_ONLY
- IOVA bars=737 dollar_bars=308 delta=122.833083 verdict=DOLLAR_BARS_DISTRIBUTION_IMPROVED_DIAGNOSTIC_ONLY
- IOVA bars=721 dollar_bars=333 delta=49.480919 verdict=DOLLAR_BARS_DISTRIBUTION_IMPROVED_DIAGNOSTIC_ONLY

## Interpretation

Dollar bars are only a data representation candidate. A positive diagnostic does not imply alpha; it only justifies a future preregistered data-transform validator.


Vedi [[Devlog-Index]] e [[Stato-Corrente]].
