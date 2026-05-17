# License Notes - Databento Equities Historical Preflight

This is a pre-query placeholder for Databento equities historical evaluation.

User-reported account state:

```text
provider: Databento
selected_product_area: equities
selected_mode: historical
free_credits_usd: 125
credit_card_attached: false
api_key_status: user-set-locally-but-not-stored
```

Pre-query notes:

- No Databento API query has been executed by this preflight.
- No API key is stored in this repository.
- Raw response retention is disabled until license/storage rights are verified.
- Dataset candidate from user-provided example: `EQUS.MINI`.
- Schema candidate from user-provided example: `trades`.

Open items before any real provider evaluation:

- Confirm Databento terms URL and account-specific data license.
- Confirm whether research storage of raw responses is allowed.
- Confirm whether normalized metadata derived from responses may be committed.
- Confirm whether `EQUS.MINI` is sufficient for small-cap provider evaluation.
- Confirm delisted symbol support, corporate-action support and symbol mapping support.
- Confirm cost estimate for one tiny historical query before execution.
