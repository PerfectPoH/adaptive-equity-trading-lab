from __future__ import annotations

import json

from src.experiments.provider_credential_preflight import inspect_credential_environment, main


def test_inspect_credential_environment_reports_missing_without_queries(monkeypatch) -> None:
    monkeypatch.delenv("DATABENTO_API_KEY", raising=False)
    monkeypatch.delenv("POLYGON_API_KEY", raising=False)

    report = inspect_credential_environment()

    assert report["status"] == "blocked"
    assert report["provider_query_performed"] is False
    assert report["network_call_performed"] is False
    assert report["secret_values_disclosed"] is False
    assert report["missing_env_vars"] == ["DATABENTO_API_KEY", "POLYGON_API_KEY"]


def test_inspect_credential_environment_reports_present_without_disclosure(monkeypatch) -> None:
    monkeypatch.setenv("DATABENTO_API_KEY", "secret-databento")
    monkeypatch.setenv("POLYGON_API_KEY", "secret-polygon")

    report = inspect_credential_environment()

    assert report["status"] == "pass"
    assert report["missing_env_vars"] == []
    assert all(item["present"] for item in report["checks"])
    assert all(item["value_disclosed"] is False for item in report["checks"])
    assert "secret-databento" not in json.dumps(report)
    assert "secret-polygon" not in json.dumps(report)


def test_main_returns_blocked_for_missing_required_env(monkeypatch, capsys) -> None:
    monkeypatch.delenv("TEST_PROVIDER_KEY", raising=False)

    code = main(["--required-env-var", "TEST_PROVIDER_KEY"])

    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == 2
    assert report["status"] == "blocked"
    assert report["missing_env_vars"] == ["TEST_PROVIDER_KEY"]
    assert report["provider_query_performed"] is False


def test_main_returns_pass_for_present_required_env_without_disclosure(monkeypatch, capsys) -> None:
    monkeypatch.setenv("TEST_PROVIDER_KEY", "secret-value")

    code = main(["--required-env-var", "TEST_PROVIDER_KEY"])

    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == 0
    assert report["status"] == "pass"
    assert report["missing_env_vars"] == []
    assert "secret-value" not in captured.out
