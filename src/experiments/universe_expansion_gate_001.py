from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from src.experiments.universe_expansion_gate_validator import validate_universe_expansion_gate


RUN_ID = "UNIVERSE-EXPANSION-GATE-RUN-001"
TRIAL_ID = "UNIVERSE-EXPANSION-GATE-001"
SPEC_DIR = Path("experiments/provider_aware_research/universe_expansion_gate_20260524")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs/UNIVERSE-EXPANSION-GATE-RUN-001")
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-Universe-Expansion-Gate-001-2026-05-24.md")


def run_universe_expansion_gate_001(
    *,
    spec_dir: str | Path = SPEC_DIR,
    output_dir: str | Path = OUTPUT_DIR,
    vault_report: str | Path = VAULT_REPORT,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    gate = validate_universe_expansion_gate(spec_dir)
    _write_json(output / "gate_validation_report.json", gate)
    manifest = _read_manifest(Path(spec_dir))
    quality_rules = _read_csv(Path(spec_dir) / "universe_quality_rules.csv")
    provider_requirements = _read_csv(Path(spec_dir) / "provider_requirements.csv")
    blocked_actions = _read_csv(Path(spec_dir) / "blocked_actions.csv")
    decision = _decision(gate, manifest, quality_rules, provider_requirements, blocked_actions)
    _write_json(output / "final_decision.json", decision)
    _write_csv(output / "blocked_actions.csv", _fieldnames(blocked_actions), blocked_actions)
    _write_csv(output / "provider_requirements.csv", _fieldnames(provider_requirements), provider_requirements)
    _write_csv(output / "universe_quality_rules.csv", _fieldnames(quality_rules), quality_rules)
    _write_vault_report(Path(vault_report), decision)
    return decision


def validate_universe_expansion_gate_output(output_dir: str | Path = OUTPUT_DIR) -> dict[str, Any]:
    path = Path(output_dir)
    checks: list[dict[str, str]] = []
    required = ["gate_validation_report.json", "final_decision.json", "blocked_actions.csv", "provider_requirements.csv", "universe_quality_rules.csv"]
    _check(checks, "output_dir_exists", path.exists() and path.is_dir(), str(path))
    for filename in required:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _report(checks)
    decision = json.loads((path / "final_decision.json").read_text(encoding="utf-8"))
    gate = json.loads((path / "gate_validation_report.json").read_text(encoding="utf-8"))
    blocked = _read_csv(path / "blocked_actions.csv")
    _check(checks, "gate_passed", gate.get("status") == "pass", str(gate.get("status")))
    _check(checks, "decision_not_executable", decision.get("decision") == "UNIVERSE_EXPANSION_GATE_READY_NOT_EXECUTABLE", str(decision.get("decision")))
    _check(checks, "no_provider_query", decision.get("provider_query_performed") is False, str(decision.get("provider_query_performed")))
    _check(checks, "no_market_download", decision.get("market_data_downloaded") is False, str(decision.get("market_data_downloaded")))
    _check(checks, "no_backtest", decision.get("backtest_performed") is False, str(decision.get("backtest_performed")))
    _check(checks, "no_promotion", decision.get("promotion_allowed") is False, str(decision.get("promotion_allowed")))
    _check(checks, "blocked_actions_present", len(blocked) >= 8, f"rows={len(blocked)}")
    return _report(checks)


def _decision(
    gate: dict[str, Any],
    manifest: dict[str, Any],
    quality_rules: list[dict[str, str]],
    provider_requirements: list[dict[str, str]],
    blocked_actions: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "status": "complete" if gate.get("status") == "pass" else "blocked",
        "decision": "UNIVERSE_EXPANSION_GATE_READY_NOT_EXECUTABLE" if gate.get("status") == "pass" else "UNIVERSE_EXPANSION_GATE_FAIL",
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "min_target_universe_size": manifest.get("min_target_universe_size"),
        "max_target_universe_size": manifest.get("max_target_universe_size"),
        "quality_rule_count": len(quality_rules),
        "provider_requirement_count": len(provider_requirements),
        "blocked_action_count": len(blocked_actions),
        "provider_query_performed": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "parameter_sweep_performed": False,
        "short_selling_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
        "promotion_allowed": False,
        "next_unblocked_step": "Create a separate provider-specific universe-source probe with explicit endpoint, max calls, raw retention policy, and no backtest.",
    }


def _read_manifest(spec_dir: Path) -> dict[str, Any]:
    path = spec_dir / "universe_expansion_manifest.json"
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_vault_report(path: Path, decision: dict[str, Any]) -> None:
    text = (
        "# Report Universe Expansion Gate 001 - 2026-05-24\n\n"
        f"Decision: `{decision['decision']}`\n\n"
        "## Scope\n\n"
        "Infrastructure gate only. No provider query, market-data download, strategy backtest, parameter sweep, short selling, paper/live trading, or promotion occurred.\n\n"
        "## Requirements\n\n"
        f"- Target universe size: {decision['min_target_universe_size']} to {decision['max_target_universe_size']} symbols\n"
        f"- Quality rules: {decision['quality_rule_count']}\n"
        f"- Provider requirements: {decision['provider_requirement_count']}\n"
        f"- Blocked actions: {decision['blocked_action_count']}\n\n"
        "## Next Step\n\n"
        f"{decision['next_unblocked_step']}\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _fieldnames(rows: list[dict[str, str]]) -> list[str]:
    return list(rows[0].keys()) if rows else []


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        if not fieldnames:
            handle.write("\n")
            return
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _check(checks: list[dict[str, str]], name: str, condition: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if condition else "fail", "detail": detail})


def _report(checks: list[dict[str, str]]) -> dict[str, Any]:
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "status": "pass" if failed == 0 else "fail",
        "gate_decision": "UNIVERSE_EXPANSION_GATE_OUTPUT_PASS" if failed == 0 else "UNIVERSE_EXPANSION_GATE_OUTPUT_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Universe Expansion Gate 001.")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.validate_only:
        run_universe_expansion_gate_001()
    report = validate_universe_expansion_gate_output()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
