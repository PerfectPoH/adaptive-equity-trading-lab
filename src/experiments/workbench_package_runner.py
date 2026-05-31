from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from dashboard.lab_dashboard_data import (
    build_controlled_backtest_preview,
    inspect_workbench_strategy_package,
    validate_workbench_manifest,
)


FORBIDDEN_FLAGS = {"--paper", "--live", "--promote", "--sweep", "--retain-raw-response"}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def validate_package_for_diagnostic_run(package_dir: Path) -> dict[str, Any]:
    inspection = inspect_workbench_strategy_package(package_dir)
    reasons: list[str] = []
    if inspection["status"] != "READY_FOR_RUNNER_BUILD":
        reasons.append("package_not_ready_for_runner_build")
    command = inspection.get("command_spec", {})
    data_contract = inspection.get("data_contract", {})
    risk = inspection.get("risk_policy", {})
    if command.get("execution_allowed") is not False:
        reasons.append("command_execution_allowed_not_false")
    if risk.get("promotion_allowed") is not False:
        reasons.append("promotion_not_locked_false")
    if data_contract.get("provider_query_allowed") is True:
        reasons.append("provider_query_not_allowed_for_first_local_runner")
    if not FORBIDDEN_FLAGS.issubset(set(command.get("forbidden_flags", []))):
        reasons.append("forbidden_flags_missing")
    return {
        "package_dir": str(package_dir),
        "status": "PASS" if not reasons else "BLOCK",
        "reasons": reasons,
        "inspection_status": inspection["status"],
    }


def build_runner_final_decision(preview: dict[str, Any], validation: dict[str, Any]) -> dict[str, Any]:
    verdict = dict(preview.get("automatic_verdict", {}))
    blockers = list(verdict.get("blockers", [])) + list(validation.get("reasons", []))
    decision = "WORKBENCH_PACKAGE_RUNNER_COMPLETE_NO_PROMOTION" if not blockers else "WORKBENCH_PACKAGE_RUNNER_ARCHIVE_CURRENT_FORM"
    return {
        "decision": decision,
        "promotion_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
        "provider_query_performed": False,
        "market_data_download_performed": False,
        "backtest_performed": validation.get("status") == "PASS",
        "runner_mode": "diagnostic_local_package_runner",
        "workbench_decision": verdict.get("decision", preview.get("decision", "UNKNOWN")),
        "blockers": blockers,
        "simulated_trades": int(preview.get("simulated_trades", 0) or 0),
        "net_return_sum": preview.get("cost_breakdown", {}).get("net_return_sum"),
        "manifest_signature": preview.get("manifest_signature"),
    }


def write_vault_report(output_dir: Path, manifest: dict[str, Any], decision: dict[str, Any]) -> Path:
    report_path = output_dir / "vault_report.md"
    report_path.write_text(
        "\n".join(
            [
                "# Workbench Package Diagnostic Runner",
                "",
                "## Verdict",
                "",
                f"- decision: `{decision['decision']}`",
                f"- promotion_allowed: `{decision['promotion_allowed']}`",
                f"- provider_query_performed: `{decision['provider_query_performed']}`",
                f"- simulated_trades: `{decision['simulated_trades']}`",
                f"- net_return_sum: `{decision['net_return_sum']}`",
                "",
                "## Strategy",
                "",
                f"- name: `{manifest.get('strategy_name', 'UNKNOWN')}`",
                f"- template: `{manifest.get('template', 'UNKNOWN')}`",
                f"- universe: `{manifest.get('universe', 'UNKNOWN')}`",
                "",
                "## Governance",
                "",
                "This runner is diagnostic only. It consumes a saved Workbench package, uses local archived data, and cannot promote, paper trade, live trade, or query providers.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return report_path


def run_package_diagnostic(package_dir: Path) -> dict[str, str]:
    package_dir = Path(package_dir)
    output_dir = package_dir / "diagnostic_runner"
    output_dir.mkdir(parents=True, exist_ok=True)
    validation = validate_package_for_diagnostic_run(package_dir)
    inspection = inspect_workbench_strategy_package(package_dir)
    manifest = inspection.get("manifest", {})
    runner_audit = {
        "runner_id": "WORKBENCH-PACKAGE-DIAGNOSTIC-RUNNER-001",
        "package_dir": str(package_dir),
        "validation": validation,
        "blocked_actions": sorted(FORBIDDEN_FLAGS),
    }
    _write_json(output_dir / "runner_audit.json", runner_audit)
    if validation["status"] != "PASS":
        decision = build_runner_final_decision({"automatic_verdict": {"blockers": validation["reasons"]}}, validation)
        _write_json(output_dir / "final_decision.json", decision)
        write_vault_report(output_dir, manifest, decision)
        return {
            "output_dir": str(output_dir),
            "runner_audit_path": str(output_dir / "runner_audit.json"),
            "final_decision_path": str(output_dir / "final_decision.json"),
            "vault_report_path": str(output_dir / "vault_report.md"),
        }
    validation_rows = validate_workbench_manifest(manifest)
    preview = build_controlled_backtest_preview(manifest, validation_rows)
    pd.DataFrame(preview.get("trade_rows", [])).to_csv(output_dir / "trades.csv", index=False)
    pd.DataFrame(preview.get("equity_curve", [])).to_csv(output_dir / "equity_curve.csv", index=False)
    summary = {
        "strategy_name": preview.get("strategy_name"),
        "template": preview.get("template"),
        "simulated_trades": preview.get("simulated_trades", 0),
        "gross_return_sum": preview.get("cost_breakdown", {}).get("gross_return_sum"),
        "net_return_sum": preview.get("cost_breakdown", {}).get("net_return_sum"),
        "automatic_verdict": preview.get("automatic_verdict", {}),
    }
    _write_json(output_dir / "summary.json", summary)
    decision = build_runner_final_decision(preview, validation)
    _write_json(output_dir / "final_decision.json", decision)
    report_path = write_vault_report(output_dir, manifest, decision)
    return {
        "output_dir": str(output_dir),
        "runner_audit_path": str(output_dir / "runner_audit.json"),
        "trades_path": str(output_dir / "trades.csv"),
        "equity_curve_path": str(output_dir / "equity_curve.csv"),
        "summary_path": str(output_dir / "summary.json"),
        "final_decision_path": str(output_dir / "final_decision.json"),
        "vault_report_path": str(report_path),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-dir", type=Path, required=True)
    parser.add_argument("--paper", action="store_true")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--promote", action="store_true")
    parser.add_argument("--sweep", action="store_true")
    args = parser.parse_args(argv)
    if args.paper or args.live or args.promote or args.sweep:
        print(json.dumps({"error": "forbidden_flag_present"}, indent=2, sort_keys=True))
        return 2
    paths = run_package_diagnostic(args.package_dir)
    print(json.dumps(paths, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
