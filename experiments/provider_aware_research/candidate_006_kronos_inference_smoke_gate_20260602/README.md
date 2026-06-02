# Candidate 006 Kronos Inference Smoke Gate 001

This gate authorizes one bounded CPU smoke test only.

The smoke test may shallow-clone `shiyu-coder/Kronos` into `.external/kronos`, download `NeoQuasar/Kronos-mini` and `NeoQuasar/Kronos-Tokenizer-2k`, and run one small inference on one local OHLCV sample.

It forbids fine-tuning, batch inference, threshold optimization, portfolio backtesting, paper trading, live trading, alpha claims, and promotion.
