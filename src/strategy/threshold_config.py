from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ThresholdConfig:
    version: str
    min_scanner_score: float
    min_model_probability: float
    calibration_method: str
    model_type: str
    selection_basis: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


DEFAULT_THRESHOLD_CONFIG = ThresholdConfig(
    version="thresholds_v2026_05_08_isotonic_025",
    min_scanner_score=70,
    min_model_probability=0.25,
    calibration_method="isotonic",
    model_type="random_forest",
    selection_basis="walk_forward_validation_wf_2024",
)
