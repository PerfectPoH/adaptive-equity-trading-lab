# Polygon PIT Membership Policy Gate 001

This gate decides what the completed Polygon active-seed, liquidity, and delisted-metadata probes actually authorize.

It performs no provider query and no market-data download. It may allow a single-day liquid snapshot to be used for future diagnostics, but it must block broad historical universe backtests until listing-date support and as-of membership history are constructed and preregistered.

