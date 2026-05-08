# Risk Management

Milestone 1 uses conservative rules:

- risk at most 1% of equity per trade;
- at most 3 open positions;
- stop loss required;
- no averaging down;
- no leverage;
- no shorting.

Position size:

```text
risk_amount = equity * 0.01
shares = risk_amount / (entry_price - stop_loss)
```

Execution rules:

- signal after today's close;
- entry at next trading day's open;
- skip trade if next open is missing;
- skip trade if ATR is invalid;
- skip trade if gap exceeds `max_gap_threshold`;
- skip trade if risk/reward is invalid.
