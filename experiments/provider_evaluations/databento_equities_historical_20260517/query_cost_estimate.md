# Query Cost Estimate - Databento Equities Historical Preflight

No query has been executed.

User-reported account state:

```text
free_credits_usd: 125
credit_card_attached: false
selected_product_area: equities
selected_mode: historical
```

User-authorized free-credit cap:

```text
free_credit_authorized: true
free_credit_cap_usd: 125
payment_authorized: false
payment_cap_usd: 0
actual_query_cost_usd: 0
```

Before real execution:

- verify Databento cost preview or usage estimate for the exact query;
- avoid `ALL_SYMBOLS` for first provider probe;
- use one frozen event, one symbol, one tiny time window and a very low record limit;
- do not retain raw response until license/storage rights are confirmed;
- stop if a query would require card-backed payment or paid balance beyond the 125 USD free-credit authorization.
