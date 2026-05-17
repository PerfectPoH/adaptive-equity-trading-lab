# 2026-05-17 - Quant research architecture upgrade plan

## Contesto

Dopo la valutazione critica del framework, e' stato creato un piano spec-only per trasformare l'analisi in roadmap implementabile senza aprire nuovi trial o query provider.

## Output

Creato [[Report-Quant-Research-Architecture-Upgrade-Plan-2026-05-17]].

## Punti recepiti

- Il sistema e' un framework di ricerca/falsificazione, non un trading bot retail.
- Il rischio principale futuro e' il meta-overfitting del framework stesso.
- Execution realism e' ancora insufficiente per claim production-grade.
- Servono purging/embargo, impact model e lifecycle tracking prima di qualsiasi salto verso paper/live.

## Roadmap proposta

1. Validation integrity: purged temporal split + embargo.
2. Execution realism: square-root impact model prima di Almgren-Chriss/LOB complessi.
3. Strategy lifecycle ledger.
4. Event-driven architecture in-process prima di microservizi esterni.

## Stato

```text
SPEC ONLY
NOT IMPLEMENTED
NO PROVIDER QUERY
NO STRATEGY TRIAL OPENED
NO BACKTEST / NO OOS / NO SWEEP
NO LIVE / NO PAPER TRADING
```

## Prossimo candidato

`RESEARCH-062 - Implement purged temporal split and embargo validator`, con TDD e synthetic fixtures, senza dati market/provider e senza backtest.
