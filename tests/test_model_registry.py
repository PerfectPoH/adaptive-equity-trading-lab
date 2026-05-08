from __future__ import annotations

import csv
from pathlib import Path

from src.models.registry import register_model_artifact


def test_register_model_artifact_writes_metadata_and_append_only_registry(tmp_path: Path) -> None:
    model_path = tmp_path / "runs" / "run_001" / "model.joblib"
    model_path.parent.mkdir(parents=True)
    model_path.write_bytes(b"model-bytes")
    registry_path = tmp_path / "model_registry.csv"

    metadata_path = register_model_artifact(
        run_id="run_001",
        model_path=model_path,
        registry_path=registry_path,
        model_type="random_forest",
        calibration_method="isotonic",
        min_model_probability=0.25,
        feature_set="baseline",
        train_period="2020-2022",
        validation_period="2023",
        test_period="2024",
        params={"max_gap_threshold": 0.05},
        metrics={"validation_roc_auc": 0.61, "test_roc_auc": 0.58},
    )

    assert metadata_path == model_path.with_name("model_metadata.json")
    assert metadata_path.exists()

    rows = list(csv.DictReader(registry_path.open(newline="", encoding="utf-8")))
    assert len(rows) == 1
    row = rows[0]
    assert row["run_id"] == "run_001"
    assert row["model_path"] == str(model_path)
    assert row["model_sha256"] == "bf0f5239d583d1729f5b833e6c773435e482e9f426937a8424cf57a0de89d831"
    assert row["model_type"] == "random_forest"
    assert row["calibration_method"] == "isotonic"
    assert row["min_model_probability"] == "0.25"

    second_model_path = tmp_path / "runs" / "run_002" / "model.joblib"
    second_model_path.parent.mkdir(parents=True)
    second_model_path.write_bytes(b"other-model-bytes")
    register_model_artifact(
        run_id="run_002",
        model_path=second_model_path,
        registry_path=registry_path,
        model_type="random_forest",
        calibration_method="raw",
        min_model_probability=0.45,
        feature_set="baseline",
        train_period="2020-2022",
        validation_period="2023",
        test_period="2024",
        params={},
        metrics={},
    )

    rows = list(csv.DictReader(registry_path.open(newline="", encoding="utf-8")))
    assert [row["run_id"] for row in rows] == ["run_001", "run_002"]
