"""Runner CLI per TRIAL-STUDIO-OOS-001. Scrive gli artifact e stampa il verdetto."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dashboard.lab_dashboard_data import (  # noqa: E402
    build_strategy_factory_components,
    load_dashboard_payload,
    load_portfolio_lab_components,
)
from src.experiments.studio_oos_validation import OosConfig, run_studio_oos_validation  # noqa: E402


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--cutoff", default="2025-01-01")
    parser.add_argument("--trial-id", default="TRIAL-STUDIO-OOS-001")
    parser.add_argument("--vol-norm", action="store_true")
    parser.add_argument("--mode", default="search", choices=["search", "rule"])
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    components = load_portfolio_lab_components(limit=60) + build_strategy_factory_components(max_variants=48)
    payload = load_dashboard_payload(Path("."))
    router = payload["strategy_regime_router"]["matrix"]
    regime_map = payload["regime_map"]
    result = run_studio_oos_validation(
        components, router, regime_map,
        OosConfig(
            trial_id=args.trial_id, cutoff=args.cutoff, vol_normalize=args.vol_norm,
            selection_mode=args.mode, rule_top_k=args.top_k,
        )
    )
    slug = args.trial_id.lower().replace("trial-studio-oos-", "studio_oos_")
    out_dir = Path("experiments/runs") / f"{slug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    out_dir.mkdir(parents=True, exist_ok=True)
    curves = result.pop("curves", None)
    if curves is not None:
        curves.to_csv(out_dir / "oos_curves.csv", index=False)
    (out_dir / "oos_result.json").write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print("ARTIFACTS:", out_dir)
    print("VERDICT:", result.get("verdict", result.get("status")))
    print(json.dumps({**result.get("summary", {}), **result.get("statistical_gate", {}),
                      "capital_sim": result.get("capital_simulation_illustrative", {})}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
