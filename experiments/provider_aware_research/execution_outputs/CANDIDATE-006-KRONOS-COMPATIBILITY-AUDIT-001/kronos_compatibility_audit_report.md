# Candidate 006 Kronos Compatibility Audit 001

Decision: `CANDIDATE_006_KRONOS_COMPATIBILITY_AUDIT_COMPLETE_NO_MODEL_DOWNLOAD`

Scope: compatibility audit only. No clone, model download, inference, fine-tuning, backtest, or promotion.

## Repo Check

- Kronos repo metadata status: `reachable`.
- Head count observed: `1`.

## Local Dependencies

- python: available=`True` version/origin=`3.12.13`
- torch: available=`True` version/origin=`C:\Users\barak\Documents\Codici Scuola\adaptive-equity-trading-lab\.venv-lab\Lib\site-packages\torch\__init__.py`
- transformers: available=`True` version/origin=`C:\Users\barak\Documents\Codici Scuola\adaptive-equity-trading-lab\.venv-lab\Lib\site-packages\transformers\__init__.py`
- huggingface_hub: available=`True` version/origin=`C:\Users\barak\Documents\Codici Scuola\adaptive-equity-trading-lab\.venv-lab\Lib\site-packages\huggingface_hub\__init__.py`
- pandas: available=`True` version/origin=`C:\Users\barak\Documents\Codici Scuola\adaptive-equity-trading-lab\.venv-lab\Lib\site-packages\pandas\__init__.py`
- numpy: available=`True` version/origin=`C:\Users\barak\Documents\Codici Scuola\adaptive-equity-trading-lab\.venv-lab\Lib\site-packages\numpy\__init__.py`

## Schema

- Norgate-to-Kronos normalization passed: `True`.
- Columns: `['open', 'high', 'low', 'close', 'volume', 'amount']`.

## Blockers

- None for compatibility. A separate smoke gate is still required before any inference.

## Next Allowed Action

`create_candidate_006_kronos_inference_smoke_gate_if_dependencies_available`
