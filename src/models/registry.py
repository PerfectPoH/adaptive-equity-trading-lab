from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path


REGISTRY_FIELDS = [
    "date",
    "run_id",
    "model_path",
    "metadata_path",
    "model_sha256",
    "model_type",
    "calibration_method",
    "min_model_probability",
    "feature_set",
    "train_period",
    "validation_period",
    "test_period",
    "params",
    "metrics",
]


def register_model_artifact(
    run_id: str,
    model_path: Path,
    registry_path: Path,
    model_type: str,
    calibration_method: str,
    min_model_probability: float,
    feature_set: str,
    train_period: str,
    validation_period: str,
    test_period: str,
    params: dict[str, object],
    metrics: dict[str, object],
) -> Path:
    model_hash = _sha256_file(model_path)
    metadata_path = model_path.with_name("model_metadata.json")
    metadata = {
        "date": datetime.now().isoformat(timespec="seconds"),
        "run_id": run_id,
        "model_path": str(model_path),
        "model_sha256": model_hash,
        "model_type": model_type,
        "calibration_method": calibration_method,
        "min_model_probability": min_model_probability,
        "feature_set": feature_set,
        "train_period": train_period,
        "validation_period": validation_period,
        "test_period": test_period,
        "params": params,
        "metrics": metrics,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")

    row = {
        "date": metadata["date"],
        "run_id": run_id,
        "model_path": str(model_path),
        "metadata_path": str(metadata_path),
        "model_sha256": model_hash,
        "model_type": model_type,
        "calibration_method": calibration_method,
        "min_model_probability": min_model_probability,
        "feature_set": feature_set,
        "train_period": train_period,
        "validation_period": validation_period,
        "test_period": test_period,
        "params": json.dumps(params, sort_keys=True),
        "metrics": json.dumps(metrics, sort_keys=True),
    }
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    exists = registry_path.exists()
    with registry_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REGISTRY_FIELDS)
        if not exists or registry_path.stat().st_size == 0:
            writer.writeheader()
        writer.writerow(row)
    return metadata_path


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
