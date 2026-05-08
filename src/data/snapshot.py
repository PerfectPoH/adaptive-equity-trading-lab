from __future__ import annotations

import hashlib
from datetime import date
from pathlib import Path

import pandas as pd


SNAPSHOT_DIR = Path("data/snapshots")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot_name(symbol: str, as_of: date | None = None) -> str:
    stamp = (as_of or date.today()).isoformat()
    return f"{symbol.upper()}_{stamp}"


def save_snapshot(
    symbol: str,
    data: pd.DataFrame,
    snapshot_dir: Path | str = SNAPSHOT_DIR,
    as_of: date | None = None,
) -> tuple[Path, Path, str]:
    root = Path(snapshot_dir)
    root.mkdir(parents=True, exist_ok=True)

    base_name = snapshot_name(symbol, as_of)
    csv_path = root / f"{base_name}.csv"
    hash_path = root / f"{base_name}.sha256"

    data.to_csv(csv_path, index=True)
    digest = sha256_file(csv_path)
    hash_path.write_text(f"{digest}  {csv_path.name}\n", encoding="utf-8")
    return csv_path, hash_path, digest


def latest_snapshot(symbol: str, snapshot_dir: Path | str = SNAPSHOT_DIR) -> Path | None:
    root = Path(snapshot_dir)
    matches = sorted(root.glob(f"{symbol.upper()}_*.csv"))
    return matches[-1] if matches else None
