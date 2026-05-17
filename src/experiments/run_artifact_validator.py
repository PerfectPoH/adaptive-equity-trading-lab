from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

REQUIRED_FILES = [
    "run_manifest.json",
    "candidate_export.csv",
    "benchmark_report.csv",
    "portfolio_trade_log.csv",
    "portfolio_equity_curve.csv",
    "portfolio_rejections.csv",
    "portfolio_summary.csv",
    "small_cap_backtest_report.md",
]

REQUIRED_MANIFEST_FIELDS = ["run_id", "config_hash", "period", "universe", "extras", "trial_accounting"]
OPTIONAL_JSON_FILES = ["property_check_report.json", "bootstrap_random_baseline.json", "random_entry_sign_flip_report.json"]
OPTIONAL_MARKDOWN_FILES = ["property_check_report.md", "backtest_report.md"]
EMPTY_ALLOWED_CSV_FILES = {"portfolio_rejections.csv"}


def validate_run_artifacts(run_dir: str | Path) -> dict[str, Any]:
    path = Path(run_dir)
    checks: list[dict[str, str]] = []
    _add_check(checks, "run_dir_exists", path.exists() and path.is_dir(), str(path))
    if not path.exists() or not path.is_dir():
        return _report(path, checks)

    for filename in REQUIRED_FILES:
        file_path = path / filename
        _add_check(checks, f"required_file:{filename}", file_path.exists() and file_path.is_file(), str(file_path))

    manifest = _read_json(path / "run_manifest.json", checks, "manifest_json")
    if isinstance(manifest, dict):
        missing = [field for field in REQUIRED_MANIFEST_FIELDS if field not in manifest]
        period = manifest.get("period")
        period_ok = isinstance(period, dict) and "start" in period and "end" in period
        universe_ok = isinstance(manifest.get("universe"), list)
        extras_ok = isinstance(manifest.get("extras"), dict)
        accounting_ok = isinstance(manifest.get("trial_accounting"), dict)
        _add_check(
            checks,
            "manifest_required_fields",
            not missing and period_ok and universe_ok and extras_ok and accounting_ok,
            f"missing={missing}; period_ok={period_ok}; universe_ok={universe_ok}; extras_ok={extras_ok}; trial_accounting_ok={accounting_ok}",
        )

    for filename in REQUIRED_FILES:
        if filename.endswith(".csv") and (path / filename).exists():
            _read_csv(path / filename, checks, f"csv_readable:{filename}", allow_empty=filename in EMPTY_ALLOWED_CSV_FILES)
        if filename.endswith(".md") and (path / filename).exists():
            _read_text_file(path / filename, checks, f"markdown_readable:{filename}")

    for filename in OPTIONAL_JSON_FILES:
        file_path = path / filename
        if file_path.exists():
            _read_json(file_path, checks, f"optional_json:{filename}")

    for filename in OPTIONAL_MARKDOWN_FILES:
        file_path = path / filename
        if file_path.exists():
            _read_text_file(file_path, checks, f"optional_markdown:{filename}")

    return _report(path, checks)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = validate_run_artifacts(args.run_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate expected artifacts in an experiment run directory.")
    parser.add_argument("--run-dir", required=True, help="Run artifact directory to validate.")
    return parser


def _read_json(path: Path, checks: list[dict[str, str]], name: str) -> Any:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        _add_check(checks, name, False, f"{path}: {exc}")
        return None
    _add_check(checks, name, True, str(path))
    return payload


def _read_csv(path: Path, checks: list[dict[str, str]], name: str, allow_empty: bool = False) -> pd.DataFrame | None:
    try:
        frame = pd.read_csv(path)
    except pd.errors.EmptyDataError:
        _add_check(checks, name, allow_empty, f"{path}: empty")
        return pd.DataFrame() if allow_empty else None
    except Exception as exc:  # noqa: BLE001
        _add_check(checks, name, False, f"{path}: {exc}")
        return None
    _add_check(checks, name, (allow_empty or not frame.empty) and bool(frame.columns.tolist()), f"{path}: rows={len(frame)}; columns={len(frame.columns)}")
    return frame


def _read_text_file(path: Path, checks: list[dict[str, str]], name: str) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        _add_check(checks, name, False, f"{path}: {exc}")
        return None
    _add_check(checks, name, bool(text.strip()), f"{path}: chars={len(text)}")
    return text


def _add_check(checks: list[dict[str, str]], name: str, passed: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if passed else "fail", "detail": str(detail)})


def _report(path: Path, checks: list[dict[str, str]]) -> dict[str, Any]:
    failed = sum(1 for check in checks if check["status"] == "fail")
    passed = sum(1 for check in checks if check["status"] == "pass")
    return {
        "run_dir": str(path),
        "status": "pass" if failed == 0 else "fail",
        "summary": {"passed": passed, "failed": failed, "total": len(checks)},
        "checks": checks,
    }


if __name__ == "__main__":
    raise SystemExit(main())
