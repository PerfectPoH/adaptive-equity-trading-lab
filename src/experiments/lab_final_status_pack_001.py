from __future__ import annotations

import argparse
import csv
import html
import json
from pathlib import Path
from typing import Any


RUN_ID = "LAB-FINAL-STATUS-PACK-RUN-001"
TRIAL_ID = "LAB-FINAL-STATUS-PACK-001"
EXECUTION_OUTPUTS_DIR = Path("experiments/provider_aware_research/execution_outputs")
TRANSITION_DECISION = EXECUTION_OUTPUTS_DIR / "RESEARCH-PROGRAM-TRANSITION-POLICY-GATE-RUN-001" / "final_decision.json"
FIVE_POINT_DECISION = EXECUTION_OUTPUTS_DIR / "TRANSITION-FIVE-POINT-BATCH-RUN-001" / "final_decision.json"
OUTPUT_DIR = EXECUTION_OUTPUTS_DIR / RUN_ID
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-Lab-Final-Status-Pack-001-2026-05-25.md")


def run_lab_final_status_pack_001(
    *,
    execution_outputs_dir: str | Path = EXECUTION_OUTPUTS_DIR,
    transition_decision_path: str | Path = TRANSITION_DECISION,
    five_point_decision_path: str | Path = FIVE_POINT_DECISION,
    output_dir: str | Path = OUTPUT_DIR,
    vault_report: str | Path = VAULT_REPORT,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    ledger_rows = collect_decision_rows(execution_outputs_dir)
    phase_summary = summarize_research_phase(ledger_rows)
    transition = _read_json(Path(transition_decision_path))
    five_point = _read_json(Path(five_point_decision_path))
    operating_rules = build_risk_regime_operating_rules(transition, five_point)
    dashboard = render_dashboard_html(
        phase_summary=phase_summary,
        operating_rules=operating_rules,
        ledger_rows=ledger_rows,
    )
    decision = {
        "status": "complete",
        "decision": "LAB_FINAL_STATUS_PACK_COMPLETE",
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "completed_points": 3,
        "ledger_row_count": len(ledger_rows),
        "promoted_strategy_count": phase_summary["promoted_strategy_count"],
        "final_policy": phase_summary["final_policy"],
        "provider_query_performed": False,
        "provider_call_count": 0,
        "raw_payload_retained": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "parameter_sweep_performed": False,
        "short_selling_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
        "promotion_allowed": False,
    }

    write_research_ledger_csv(output / "research_phase_closure_ledger.csv", ledger_rows)
    _write_json(output / "research_phase_summary.json", phase_summary)
    _write_json(output / "risk_regime_operating_rules.json", operating_rules)
    (output / "lab_status_dashboard.html").write_text(dashboard, encoding="utf-8")
    _write_json(output / "final_decision.json", decision)
    _write_vault_report(Path(vault_report), decision, phase_summary, operating_rules)
    return decision


def collect_decision_rows(execution_outputs_dir: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(Path(execution_outputs_dir).glob("*/final_decision.json")):
        payload = _read_json(path)
        rows.append(
            {
                "trial_id": str(payload.get("trial_id", "")),
                "run_id": str(payload.get("run_id", path.parent.name)),
                "decision": str(payload.get("decision", "")),
                "promotion_allowed": bool(payload.get("promotion_allowed", False)),
                "provider_query_performed": bool(payload.get("provider_query_performed", False)),
                "backtest_performed": bool(payload.get("backtest_performed", False)),
                "short_selling_performed": bool(payload.get("short_selling_performed", False)),
                "source_file": str(path),
            }
        )
    return rows


def summarize_research_phase(decision_rows: list[dict[str, Any]]) -> dict[str, Any]:
    promoted = [row for row in decision_rows if row.get("promotion_allowed") is True]
    decisions = [str(row.get("decision", "")) for row in decision_rows]
    blockers: list[str] = []
    if any("DELISTED" in decision or "ACTIVE_ONLY" in decision for decision in decisions):
        blockers.append("survivorship_or_pit_blocker")
    if any("ALPHAVANTAGE" in decision or "INTRINIO" in decision or "PEAD" in decision for decision in decisions):
        blockers.append("earnings_point_in_time_data_blocker")
    if any("ROBUSTNESS" in decision for decision in decisions):
        blockers.append("outlier_dependency_blocker")
    if not blockers:
        blockers.append("no_promoted_strategy")
    return {
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "decision_count": len(decision_rows),
        "promoted_strategy_count": len(promoted),
        "smallcap_free_data_directional_research_status": "PAUSED",
        "final_policy": "RISK_REGIME_ENGINE_ONLY",
        "primary_blockers": sorted(set(blockers)),
        "provider_query_rows": sum(1 for row in decision_rows if row.get("provider_query_performed") is True),
        "backtest_rows": sum(1 for row in decision_rows if row.get("backtest_performed") is True),
        "short_selling_rows": sum(1 for row in decision_rows if row.get("short_selling_performed") is True),
        "promotion_allowed": False,
    }


def build_risk_regime_operating_rules(transition_decision: dict[str, Any], five_point_decision: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "mode": "RISK_REGIME_ENGINE",
        "promotion_allowed": False,
        "allowed_actions": {
            "etf_largecap_risk_regime_diagnostics": bool(transition_decision.get("etf_largecap_risk_regime_lab_allowed", True)),
            "smallcap_microstructure_diagnostics": bool(transition_decision.get("smallcap_microstructure_diagnostic_allowed", True)),
            "data_quality_diagnostics": True,
            "portfolio_risk_diagnostics": True,
        },
        "forbidden_actions": {
            "smallcap_free_data_directional_alpha": not bool(transition_decision.get("smallcap_free_data_directional_research_allowed", False)),
            "short_selling": True,
            "strategy_promotion_without_new_gate": True,
            "provider_query_without_pre_run_gate": True,
            "paper_or_live_trading": True,
        },
        "source_decisions": {
            "transition_policy": str(transition_decision.get("decision", "")),
            "five_point_batch": str(five_point_decision.get("decision", "")),
        },
    }


def render_dashboard_html(
    *,
    phase_summary: dict[str, Any],
    operating_rules: dict[str, Any],
    ledger_rows: list[dict[str, Any]],
) -> str:
    table_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(str(row.get('trial_id', '')))}</td>"
        f"<td>{html.escape(str(row.get('decision', '')))}</td>"
        f"<td>{html.escape(str(row.get('promotion_allowed', False)))}</td>"
        "</tr>"
        for row in ledger_rows
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Adaptive Equity Trading Lab Status</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #1f2933; }}
    h1, h2 {{ margin-bottom: 8px; }}
    .band {{ border: 1px solid #ccd5df; border-radius: 6px; padding: 16px; margin: 16px 0; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
    th, td {{ border-bottom: 1px solid #d8dee6; padding: 8px; text-align: left; }}
    code {{ background: #eef2f6; padding: 2px 4px; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>Adaptive Equity Trading Lab Status</h1>
  <section class="band">
    <h2>Research Phase Closure</h2>
    <p>Final policy: <code>{html.escape(str(phase_summary.get("final_policy", "")))}</code></p>
    <p>Promoted strategies: <code>{html.escape(str(phase_summary.get("promoted_strategy_count", 0)))}</code></p>
    <p>Small-cap free-data directional research: <code>{html.escape(str(phase_summary.get("smallcap_free_data_directional_research_status", "")))}</code></p>
  </section>
  <section class="band">
    <h2>Risk/Regime Operating Rules</h2>
    <p>Mode: <code>{html.escape(str(operating_rules.get("mode", "")))}</code></p>
    <p>Promotion allowed: <code>{html.escape(str(operating_rules.get("promotion_allowed", False)))}</code></p>
  </section>
  <section class="band">
    <h2>Final Research Ledger</h2>
    <table>
      <thead><tr><th>Trial</th><th>Decision</th><th>Promotion Allowed</th></tr></thead>
      <tbody>{table_rows}</tbody>
    </table>
  </section>
</body>
</html>
"""


def validate_lab_final_status_pack_output(output_dir: str | Path = OUTPUT_DIR) -> dict[str, Any]:
    path = Path(output_dir)
    checks: list[dict[str, str]] = []
    required = [
        "research_phase_closure_ledger.csv",
        "research_phase_summary.json",
        "risk_regime_operating_rules.json",
        "lab_status_dashboard.html",
        "final_decision.json",
    ]
    _check(checks, "output_dir_exists", path.exists() and path.is_dir(), str(path))
    for filename in required:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _validation_report(checks)
    decision = _read_json(path / "final_decision.json")
    rules = _read_json(path / "risk_regime_operating_rules.json")
    dashboard = (path / "lab_status_dashboard.html").read_text(encoding="utf-8")
    _check(checks, "completed_three_points", decision.get("completed_points") == 3, str(decision.get("completed_points")))
    _check(checks, "provider_query_not_performed", decision.get("provider_query_performed") is False, str(decision.get("provider_query_performed")))
    _check(checks, "backtest_not_performed", decision.get("backtest_performed") is False, str(decision.get("backtest_performed")))
    _check(checks, "promotion_blocked", decision.get("promotion_allowed") is False, str(decision.get("promotion_allowed")))
    _check(checks, "risk_mode_set", rules.get("mode") == "RISK_REGIME_ENGINE", str(rules.get("mode")))
    _check(checks, "dashboard_sections_present", all(section in dashboard for section in ["Research Phase Closure", "Risk/Regime Operating Rules", "Final Research Ledger"]), "sections")
    return _validation_report(checks)


def write_research_ledger_csv(path: str | Path, rows: list[dict[str, Any]]) -> None:
    columns = [
        "trial_id",
        "run_id",
        "decision",
        "promotion_allowed",
        "provider_query_performed",
        "backtest_performed",
        "short_selling_performed",
        "source_file",
    ]
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def _write_vault_report(path: Path, decision: dict[str, Any], summary: dict[str, Any], rules: dict[str, Any]) -> None:
    lines = [
        "# Report Lab Final Status Pack 001 - 2026-05-25",
        "",
        f"Decision: `{decision['decision']}`",
        "",
        "## Three Points",
        "",
        "1. Research phase closure ledger written.",
        "2. Risk/regime operating rules written.",
        "3. Dashboard/status artifact written.",
        "",
        "## Final Policy",
        "",
        f"- Policy: `{summary['final_policy']}`",
        f"- Promoted strategies: {summary['promoted_strategy_count']}",
        f"- Small-cap free-data directional research: `{summary['smallcap_free_data_directional_research_status']}`",
        f"- Risk/regime mode: `{rules['mode']}`",
        "",
        "## Guardrails",
        "",
        "- Provider query: false",
        "- Market-data download: false",
        "- New backtest: false",
        "- Short selling: false",
        "- Paper/live trading: false",
        "- Strategy promotion: false",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _check(checks: list[dict[str, str]], name: str, condition: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if condition else "fail", "detail": detail})


def _validation_report(checks: list[dict[str, str]]) -> dict[str, Any]:
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "status": "pass" if failed == 0 else "fail",
        "gate_decision": "LAB_FINAL_STATUS_PACK_OUTPUT_PASS" if failed == 0 else "LAB_FINAL_STATUS_PACK_OUTPUT_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run LAB-FINAL-STATUS-PACK-001.")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.validate_only:
        run_lab_final_status_pack_001()
    report = validate_lab_final_status_pack_output()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
