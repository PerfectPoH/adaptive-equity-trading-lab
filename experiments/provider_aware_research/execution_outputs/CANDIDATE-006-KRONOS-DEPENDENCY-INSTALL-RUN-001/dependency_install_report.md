# CANDIDATE-006 Kronos Dependency Install Run 001

Run timestamp UTC: `2026-06-02T15:56:35.1303870Z`

This run executed only the dependency installation scope approved by `candidate_006_kronos_dependency_install_gate_20260602`.

## Installed Runtime

- `torch`: `2.12.0+cpu`
- `transformers`: `5.9.0`
- `huggingface_hub`: `1.17.0`
- `tokenizers`: `0.22.2`
- `safetensors`: `0.7.0`
- CUDA available: `False`

## Scope Controls

- Git clone performed: `False`
- Model download performed: `False`
- Kronos inference performed: `False`
- Fine-tuning performed: `False`
- Backtest performed: `False`
- Signal generation performed: `False`
- Promotion allowed: `False`

## Post-Install Audit

The compatibility audit now sees the previously missing Kronos runtime dependencies. Dependency blockers are cleared for compatibility only.

This does not authorize model loading, inference, feature generation, fine-tuning, backtesting, paper trading, live trading, or promotion.

## Next Allowed Action

Create a separate Kronos inference smoke gate before any repository clone, model download, model loading, inference, feature generation, or backtest.
