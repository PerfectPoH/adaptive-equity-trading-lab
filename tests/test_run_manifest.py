from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.experiments.run_manifest import (
    SCHEMA_VERSION,
    build_run_manifest,
    compute_config_hash,
    manifest_to_dict,
    write_run_manifest_json,
)


@dataclass(frozen=True)
class _NestedConfig:
    threshold: float = 0.5
    enabled: bool = True


@dataclass(frozen=True)
class _DummyConfig:
    name: str = "default"
    risk_fraction: float = 0.01
    nested: _NestedConfig = _NestedConfig()


_FIXED_TS = "2026-05-11T00:00:00+00:00"


def _build_test_manifest(config: object = _DummyConfig(), **overrides: object):
    defaults = dict(
        run_id="run_test",
        created_at=_FIXED_TS,
        git_commit="abc123",
        host="testhost",
        detect_git=False,
        detect_host=False,
    )
    defaults.update(overrides)
    return build_run_manifest(config, **defaults)


def test_compute_config_hash_is_deterministic() -> None:
    assert compute_config_hash(_DummyConfig()) == compute_config_hash(_DummyConfig())


def test_compute_config_hash_changes_when_parameter_changes() -> None:
    base = compute_config_hash(_DummyConfig())
    changed = compute_config_hash(_DummyConfig(risk_fraction=0.02))
    assert base != changed


def test_compute_config_hash_changes_when_nested_parameter_changes() -> None:
    base = compute_config_hash(_DummyConfig())
    changed = compute_config_hash(_DummyConfig(nested=_NestedConfig(threshold=0.6)))
    assert base != changed


def test_compute_config_hash_ignores_dict_key_order() -> None:
    assert compute_config_hash({"a": 1, "b": 2}) == compute_config_hash({"b": 2, "a": 1})


def test_compute_config_hash_handles_paths_and_dataclasses() -> None:
    config = {"path": Path("/tmp/foo"), "nested": _NestedConfig()}
    assert compute_config_hash(config) == compute_config_hash(config)


def test_build_run_manifest_populates_required_fields() -> None:
    manifest = _build_test_manifest(
        universe=["AAA", "BBB"],
        period_start="2024-01-01",
        period_end="2024-12-31",
    )
    assert manifest.run_id == "run_test"
    assert manifest.config_hash == compute_config_hash(_DummyConfig())
    assert manifest.created_at == _FIXED_TS
    assert manifest.universe == ["AAA", "BBB"]
    assert manifest.period == {"start": "2024-01-01", "end": "2024-12-31"}
    assert manifest.git_commit == "abc123"
    assert manifest.host == "testhost"
    assert manifest.schema_version == SCHEMA_VERSION


def test_build_run_manifest_generates_run_id_when_omitted() -> None:
    manifest = build_run_manifest(
        _DummyConfig(),
        created_at=_FIXED_TS,
        detect_git=False,
        detect_host=False,
    )
    assert manifest.run_id.startswith("run_")
    assert len(manifest.run_id) > len("run_")


def test_build_run_manifest_serializes_nested_dataclass() -> None:
    manifest = _build_test_manifest()
    assert manifest.config["nested"]["threshold"] == 0.5
    assert manifest.config["nested"]["enabled"] is True
    assert manifest.config["risk_fraction"] == 0.01
    assert manifest.config["name"] == "default"


def test_build_run_manifest_keeps_optional_detection_off_when_requested() -> None:
    manifest = build_run_manifest(
        _DummyConfig(),
        run_id="run_x",
        created_at=_FIXED_TS,
        detect_git=False,
        detect_host=False,
    )
    assert manifest.git_commit is None
    assert manifest.host is None


def test_build_run_manifest_keeps_explicit_extras() -> None:
    manifest = _build_test_manifest(extras={"note": "smoke"})
    assert manifest.extras == {"note": "smoke"}


def test_manifest_to_dict_is_round_trip_safe() -> None:
    manifest = _build_test_manifest(universe=["AAA"], period_start="2024-01-01", period_end="2024-01-31")
    payload = manifest_to_dict(manifest)
    assert payload["run_id"] == manifest.run_id
    assert payload["config_hash"] == manifest.config_hash
    assert payload["period"] == manifest.period
    assert payload["config"]["nested"]["threshold"] == 0.5


def test_write_run_manifest_json_creates_stable_file(tmp_path: Path) -> None:
    manifest = _build_test_manifest(
        universe=["AAA"],
        period_start="2024-01-01",
        period_end="2024-01-31",
    )
    path = write_run_manifest_json(manifest, tmp_path / "run_manifest.json")
    assert path.exists()
    raw = path.read_text(encoding="utf-8")
    assert raw.endswith("\n")
    payload = json.loads(raw)
    assert payload["run_id"] == "run_test"
    assert payload["config_hash"] == manifest.config_hash
    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["config"]["name"] == "default"
    assert payload["universe"] == ["AAA"]
    assert payload["period"] == {"start": "2024-01-01", "end": "2024-01-31"}


def test_write_run_manifest_json_two_runs_differ_only_on_run_id_and_timestamp(tmp_path: Path) -> None:
    cfg = _DummyConfig()
    first = build_run_manifest(
        cfg,
        run_id="run_a",
        created_at=_FIXED_TS,
        git_commit="commit_a",
        host="host_a",
        detect_git=False,
        detect_host=False,
        universe=["AAA"],
        period_start="2024-01-01",
        period_end="2024-01-31",
    )
    second = build_run_manifest(
        cfg,
        run_id="run_b",
        created_at="2026-05-11T01:00:00+00:00",
        git_commit="commit_a",
        host="host_a",
        detect_git=False,
        detect_host=False,
        universe=["AAA"],
        period_start="2024-01-01",
        period_end="2024-01-31",
    )
    assert first.config_hash == second.config_hash
    assert first.run_id != second.run_id
    assert first.created_at != second.created_at
