# Candidate 006 Kronos Batch Feature Gate 001

This gate authorizes one batch feature-generation run only.

It may read the frozen Candidate 005 `symbol` and `signal_date` pairs, read local Norgate OHLCV history for those symbols, and produce Kronos-mini forecast feature rows.

It does not authorize realized-return input, threshold optimization, reranking, portfolio backtesting, fine-tuning, paper trading, live trading, alpha claims, or promotion.
