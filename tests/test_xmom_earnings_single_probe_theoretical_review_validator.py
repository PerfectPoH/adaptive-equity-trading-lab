from __future__ import annotations

import json
from pathlib import Path

from src.experiments.xmom_earnings_single_probe_theoretical_review_validator import (
    main,
    validate_xmom_earnings_single_probe_theoretical_review,
)


REVIEW_DIR = Path("experiments/provider_aware_research/xmom_earnings_single_probe_theoretical_review_20260521")


def test_theoretical_review_validator_passes_real_artifact() -> None:
    report = validate_xmom_earnings_single_probe_theoretical_review(REVIEW_DIR)

    assert report["status"] == "pass"
    assert report["decision"] == "XMOM_EARNINGS_SINGLE_PROBE_THEORETICAL_REVIEW_PASS"
    assert report["approval_granted"] is False
    assert report["provider_query_performed"] is False
    assert report["summary"]["failed"] == 0


def test_theoretical_review_validator_fails_if_review_marked_approved(tmp_path: Path) -> None:
    review = _copy_review(tmp_path)
    manifest_path = review / "theoretical_review_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["status"] = "APPROVED"
    manifest["approval_granted"] = True
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = validate_xmom_earnings_single_probe_theoretical_review(review)

    assert report["status"] == "fail"
    assert any(check["name"] == "manifest_review_identity" and check["status"] == "fail" for check in report["checks"])
    assert any(check["name"] == "manifest_not_approved_or_prepared" and check["status"] == "fail" for check in report["checks"])


def test_theoretical_review_validator_fails_if_provider_query_performed(tmp_path: Path) -> None:
    review = _copy_review(tmp_path)
    manifest_path = review / "theoretical_review_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["provider_query_performed"] = True
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = validate_xmom_earnings_single_probe_theoretical_review(review)

    assert report["status"] == "fail"
    assert any(check["name"] == "manifest_no_execution_flags" and check["status"] == "fail" for check in report["checks"])


def test_theoretical_review_validator_fails_if_intrinio_not_primary(tmp_path: Path) -> None:
    review = _copy_review(tmp_path)
    provider_review = review / "provider_candidate_review.csv"
    provider_review.write_text(
        provider_review.read_text(encoding="utf-8").replace(
            "Intrinio,primary_candidate",
            "Intrinio,secondary_candidate",
        ),
        encoding="utf-8",
    )

    report = validate_xmom_earnings_single_probe_theoretical_review(review)

    assert report["status"] == "fail"
    assert any(check["name"] == "provider_review_intrinio_primary" and check["status"] == "fail" for check in report["checks"])


def test_theoretical_review_validator_fails_if_dmt_not_purged(tmp_path: Path) -> None:
    review = _copy_review(tmp_path)
    policy = review / "timestamp_mapping_policy.csv"
    policy.write_text(
        policy.read_text(encoding="utf-8").replace(
            "local_time_between_09_30_and_16_00,DMT,purge",
            "local_time_between_09_30_and_16_00,DMT,allow_candidate",
        ),
        encoding="utf-8",
    )

    report = validate_xmom_earnings_single_probe_theoretical_review(review)

    assert report["status"] == "fail"
    assert any(check["name"] == "timestamp_policy_dmt_and_unspecified_purged" and check["status"] == "fail" for check in report["checks"])


def test_theoretical_review_validator_fails_if_query_unblocked(tmp_path: Path) -> None:
    review = _copy_review(tmp_path)
    blocked = review / "blocked_actions.csv"
    blocked.write_text(
        blocked.read_text(encoding="utf-8").replace(
            "query_provider,blocked",
            "query_provider,allowed",
        ),
        encoding="utf-8",
    )

    report = validate_xmom_earnings_single_probe_theoretical_review(review)

    assert report["status"] == "fail"
    assert any(check["name"] == "blocked_all_actions_blocked" and check["status"] == "fail" for check in report["checks"])


def test_theoretical_review_validator_cli_exit_codes(tmp_path: Path) -> None:
    review = _copy_review(tmp_path)
    assert main(["--review-dir", str(review)]) == 0

    (review / "review_sources.csv").unlink()

    assert main(["--review-dir", str(review)]) == 1


def _copy_review(tmp_path: Path) -> Path:
    target = tmp_path / "review"
    target.mkdir()
    for item in REVIEW_DIR.iterdir():
        target.joinpath(item.name).write_text(item.read_text(encoding="utf-8"), encoding="utf-8")
    return target
