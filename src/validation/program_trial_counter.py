"""Trial counter di programma (RISK-042, audit B3/D3).

Conta i RUN reali eseguiti, per famiglia e totali, dalle directory in
``experiments/runs``. Da usare come multiplicita' nel DSR al posto delle
costanti dichiarate: la multiplicita' onesta e' quante volte il programma
ha guardato i dati, non quante il singolo trial dichiara.
"""

from __future__ import annotations

import re
from pathlib import Path

RUNS_DIR = Path("experiments/runs")

# Una famiglia = un'ipotesi guardata piu' volte. Il run timestamped e' un look.
FAMILY_PATTERNS: dict[str, str] = {
    "studio_oos": r"^studio_oos_",
    "true_etf": r"^true_etf_",
    "kronos_defense": r"^kronos_defense_",
    "house_trial": r"^house_trial_",
    "honest_baselines": r"^honest_baselines_",
    "pctrl": r"^pctrl_",
    "regime_index": r"^regime_index_",
}


def count_runs(*, root: Path = Path(".")) -> dict[str, int]:
    runs_dir = Path(root) / RUNS_DIR
    if not runs_dir.exists():
        return {"total": 0}
    names = [p.name for p in runs_dir.iterdir() if p.is_dir()]
    counts = {family: sum(1 for n in names if re.match(pattern, n)) for family, pattern in FAMILY_PATTERNS.items()}
    counts["total"] = len(names)
    return counts


def program_trial_count(family: str, *, root: Path = Path(".")) -> int:
    """Multiplicita' onesta per un nuovo run della famiglia: run gia' fatti + 1."""

    counts = count_runs(root=root)
    return max(2, int(counts.get(family, 0)) + 1)


def program_wide_trial_count(*, root: Path = Path(".")) -> int:
    """Multiplicita' a livello di programma: tutti i look del lab."""

    return max(2, int(count_runs(root=root).get("total", 0)))
