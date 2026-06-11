# Devlog - Credential preflight env-file pass - 2026-05-18

Extended provider credential preflight to inspect `.env` without disclosing values.

```text
CREDENTIAL_PREFLIGHT_ENV_FILE_PASS
DATABENTO_API_KEY: present via env-file
POLYGON_API_KEY: present via env-file
NO_SECRET_DISCLOSURE
NO_PROVIDER_QUERY
NO_NETWORK_CALL
```

Updated credential result artifact and manual/dry-run preflight state. Aggregate dry-run preflight remains blocked because non-credential gates remain unresolved.


Vedi [[Devlog-Index]] e [[Stato-Corrente]].
