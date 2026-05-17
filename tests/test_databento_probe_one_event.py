from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "experiments" / "databento_probe_one_event.py"
SPEC = importlib.util.spec_from_file_location("databento_probe_one_event", MODULE_PATH)
assert SPEC is not None
databento_probe = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = databento_probe
SPEC.loader.exec_module(databento_probe)


def test_auto_uses_env_file_when_process_environment_is_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABENTO_API_KEY", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("DATABENTO_API_KEY=file-key\n", encoding="utf-8")

    api_key, diagnostics = databento_probe._resolve_databento_api_key("auto", env_file)

    assert api_key == "file-key"
    assert diagnostics["api_key_source_resolved"] == "env-file"
    assert diagnostics["api_key_fingerprint"] == databento_probe._fingerprint_secret("file-key")
    assert diagnostics["env_file_key_present"] is True
    assert diagnostics["environment_key_present"] is False
    assert "file-key" not in str(diagnostics)


def test_auto_uses_process_environment_when_env_file_is_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABENTO_API_KEY", "environment-key")
    env_file = tmp_path / ".env"

    api_key, diagnostics = databento_probe._resolve_databento_api_key("auto", env_file)

    assert api_key == "environment-key"
    assert diagnostics["api_key_source_resolved"] == "environment"
    assert diagnostics["api_key_fingerprint"] == databento_probe._fingerprint_secret("environment-key")
    assert diagnostics["env_file_exists"] is False
    assert diagnostics["environment_key_present"] is True
    assert "environment-key" not in str(diagnostics)


def test_auto_rejects_conflicting_process_and_env_file_keys(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABENTO_API_KEY", "environment-key")
    env_file = tmp_path / ".env"
    env_file.write_text("DATABENTO_API_KEY=file-key\n", encoding="utf-8")

    with pytest.raises(databento_probe.ApiKeySourceError) as exc_info:
        databento_probe._resolve_databento_api_key("auto", env_file)

    assert exc_info.value.code == "DATABENTO_API_KEY_SOURCE_CONFLICT"
    assert exc_info.value.diagnostics["api_key_source_resolved"] == "conflict"
    assert exc_info.value.diagnostics["api_key_fingerprint"] == ""
    assert exc_info.value.diagnostics["environment_key_fingerprint"] == databento_probe._fingerprint_secret("environment-key")
    assert exc_info.value.diagnostics["env_file_key_fingerprint"] == databento_probe._fingerprint_secret("file-key")
    assert "environment-key" not in str(exc_info.value.diagnostics)
    assert "file-key" not in str(exc_info.value.diagnostics)


def test_explicit_env_file_source_can_be_selected_when_environment_differs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DATABENTO_API_KEY", "environment-key")
    env_file = tmp_path / ".env"
    env_file.write_text("DATABENTO_API_KEY=file-key\n", encoding="utf-8")

    api_key, diagnostics = databento_probe._resolve_databento_api_key("env-file", env_file)

    assert api_key == "file-key"
    assert diagnostics["api_key_source_requested"] == "env-file"
    assert diagnostics["api_key_source_resolved"] == "env-file"
    assert diagnostics["api_key_fingerprint"] == databento_probe._fingerprint_secret("file-key")


def test_explicit_environment_source_can_be_selected_when_env_file_differs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DATABENTO_API_KEY", "environment-key")
    env_file = tmp_path / ".env"
    env_file.write_text("DATABENTO_API_KEY=file-key\n", encoding="utf-8")

    api_key, diagnostics = databento_probe._resolve_databento_api_key("environment", env_file)

    assert api_key == "environment-key"
    assert diagnostics["api_key_source_requested"] == "environment"
    assert diagnostics["api_key_source_resolved"] == "environment"
    assert diagnostics["api_key_fingerprint"] == databento_probe._fingerprint_secret("environment-key")
