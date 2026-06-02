# Candidate 006 Kronos Dependency Plan 001

Decision: `KRONOS_ADAPTER_READY_DEPENDENCIES_BLOCK_INFERENCE`

The Kronos adapter and schema contract are ready, but inference is blocked because local ML dependencies are missing.

## Missing Dependencies

- `torch`: future Kronos model inference (missing).
- `transformers`: future Hugging Face model loading (missing).
- `huggingface_hub`: future model/tokenizer retrieval (missing).

## Safe Next Steps

- Create a dependency installation gate before any pip install.
- Prefer CPU-only Kronos-mini smoke before any GPU or larger model.
- Keep first inference to one symbol and one forecast path only.
- Do not connect Kronos output to Candidate 005 until inference smoke output schema is archived.

## Next Allowed Action

`create_candidate_006_dependency_install_gate_if_user_approves`
