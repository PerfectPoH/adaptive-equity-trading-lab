# Query Cost Estimate

```text
INTRINIO_STARTER_PREFLIGHT
PROVIDER_QUERY_NOT_EXECUTED
NO_COST_AUTHORIZED
NO_API_KEY_USED
```

Estimated query cost for this preflight is `0 USD` because no provider API was queried.

Before real execution, confirm:

- whether the Starter Plan trial requires a credit card;
- whether the trial has API unit limits;
- whether historical stock prices, delisted securities, dividends/splits and adjustment factors are included in the active trial;
- whether endpoint calls are billable during the trial;
- whether there is any automatic renewal or paid conversion.

Pre-query hard cap:

```text
payment_authorized: false
payment_cap_usd: 0
```

If any query would incur cost, stop until explicit user approval.

User-confirmed pre-probe state:

```text
trial_type: free_trial
credit_card_attached: false
payment_authorized: false
payment_cap_usd: 0
```
