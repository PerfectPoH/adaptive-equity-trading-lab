# Polygon Active Universe Seed 001

This run builds a derived active common-stock reference seed from Polygon/Massive ticker metadata.

It resolves the distinction exposed by the previous universe quality probe: active rows are not expected to populate `delisted_utc`, so this seed may pass without that field. This does not relax the broader research governance. A separate survivorship/delisted-symbol audit and a separate liquidity/price availability probe are required before any strategy backtest.

