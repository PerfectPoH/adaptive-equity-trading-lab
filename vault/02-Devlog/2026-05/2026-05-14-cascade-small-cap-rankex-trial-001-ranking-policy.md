---
tipo: devlog
data: 2026-05-14
agente: cascade
topic: small-cap-rankex-trial-001-ranking-policy
tags: [devlog, small-cap, rankex, trial-accounting, tdd]
---

# 2026-05-14 - TRIAL-RANKEX-001 ranking policy TDD

## Obiettivo

Implementare solo la ranking policy deterministica pre-registrata per `TRIAL-RANKEX-001`, senza eseguire backtest, sweep o paper trading.

## RED

Aggiunto test:

```text
tests/test_small_cap_portfolio_backtester.py::test_portfolio_backtester_uses_preregistered_rankex_tie_breakers
```

Il test falliva perche' il portfolio backtester, a parita' di `small_cap_scanner_score`, ordinava alfabeticamente e sceglieva `AAA` invece del candidato selezionato dai tie-breaker pre-registrati.

## GREEN

Implementata in `src/backtest/small_cap_portfolio_backtester.py` la policy:

```text
1. small_cap_scanner_score desc
2. relative_volume_20d desc
3. open_to_close_return desc
4. symbol asc
```

La policy si applica solo quando `rank_column == "small_cap_scanner_score"`. Gli altri `rank_column` mantengono il comportamento precedente: score desc, symbol asc.

## Verifica

```text
pytest tests/test_small_cap_portfolio_backtester.py::test_portfolio_backtester_uses_preregistered_rankex_tie_breakers -q -> 1 passed
pytest tests/test_small_cap_portfolio_backtester.py -q -> 15 passed
pytest -q -> 177 passed
```

## Governance

Stato trial:

```text
TRIAL-RANKEX-001 IMPLEMENTATION READY / NOT RUN / NOT PROMOTED
```

Non sono stati eseguiti esperimenti storici, sweep, OOS o paper trading.

## Prossimo passo consentito

Wiring esplicito del payload `trial_accounting` per una futura run autorizzata, oppure preparazione report template, sempre senza sweep discrezionali.

Vedi [[Report-Small-Cap-RankEx-Trial-001-Preregistration-2026-05-13]], [[small-cap-ranking-exits-research-track]], [[2026-05-13-cascade-small-cap-rankex-trial-001-preregistration]], [[Roadmap-Master]], [[backlog]].
