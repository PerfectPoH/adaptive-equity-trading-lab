"""Run manifest small-cap.

Genera un manifest deterministico per ogni run del runner storico small-cap.

Lo scopo e' chiudere RISK-023 (overfitting manuale non tracciato): ogni run
deve poter essere identificato da `run_id` univoco, da un `config_hash`
deterministico sui parametri, e dal periodo/simboli usati. Cosi' diventa
possibile riconoscere sweep ripetuti sulla stessa configurazione e calcolare
in futuro Deflated Sharpe Ratio o Probability of Backtest Overfitting.

Note di design:
- l'hash e' calcolato su una rappresentazione JSON con chiavi ordinate, quindi
  e' stabile fra interpreti e ordinamenti diversi dei campi;
- nested dataclass vengono serializzati ricorsivamente via ``dataclasses.asdict``;
- ``git_commit`` e ``host`` sono best-effort: se non disponibili restano ``None``
  invece di sollevare;
- il file scritto su disco e' un JSON sort-keys+indent stabile, cosi' due run
  con la stessa configurazione producono file confrontabili byte-per-byte
  (a meno di ``run_id`` e ``created_at``).
"""
from __future__ import annotations

import hashlib
import json
import socket
import subprocess
import uuid
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1"


@dataclass(frozen=True)
class RunManifest:
    run_id: str
    config_hash: str
    created_at: str
    schema_version: str
    config: dict[str, Any]
    universe: list[str]
    period: dict[str, str | None]
    git_commit: str | None
    host: str | None
    trial_accounting: dict[str, Any] = field(default_factory=dict)
    extras: dict[str, Any] = field(default_factory=dict)


def _to_jsonable(obj: Any) -> Any:
    if is_dataclass(obj) and not isinstance(obj, type):
        return _to_jsonable(asdict(obj))
    if isinstance(obj, dict):
        return {str(key): _to_jsonable(value) for key, value in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_to_jsonable(item) for item in obj]
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    return str(obj)


def compute_config_hash(config: Any) -> str:
    """Hash deterministico SHA-256 della config.

    Accetta dataclass annidati, dict, sequenze, ``Path`` e tipi base. L'hash
    cambia se cambia qualunque parametro, ed e' stabile rispetto all'ordine
    delle chiavi nei dict.
    """
    payload = _to_jsonable(config)
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _detect_git_commit(repo_path: Path | str | None = None) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_path) if repo_path is not None else None,
            capture_output=True,
            text=True,
            check=False,
            timeout=2,
        )
    except (FileNotFoundError, subprocess.SubprocessError, OSError):
        return None
    if completed.returncode != 0:
        return None
    commit = completed.stdout.strip()
    return commit or None


def _detect_host() -> str | None:
    try:
        host = socket.gethostname()
    except OSError:
        return None
    return host or None


def _normalise_timestamp(value: str | datetime | None) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def build_run_manifest(
    config: Any,
    *,
    universe: list[str] | None = None,
    period_start: str | None = None,
    period_end: str | None = None,
    run_id: str | None = None,
    created_at: str | datetime | None = None,
    git_commit: str | None = None,
    host: str | None = None,
    trial_accounting: dict[str, Any] | None = None,
    extras: dict[str, Any] | None = None,
    repo_path: Path | str | None = None,
    detect_git: bool = True,
    detect_host: bool = True,
) -> RunManifest:
    """Costruisce un :class:`RunManifest` deterministico.

    Tutti i campi context-dependent (run_id, created_at, git_commit, host)
    possono essere passati esplicitamente per ottenere manifest stabili nei
    test. Se non passati e ``detect_*`` e' ``True``, li rileva best-effort.
    """
    config_payload = _to_jsonable(config)
    config_hash = compute_config_hash(config)

    if run_id is None:
        run_id = f"run_{uuid.uuid4().hex[:12]}"

    created_at_str = _normalise_timestamp(created_at)

    resolved_git = git_commit
    if resolved_git is None and detect_git:
        resolved_git = _detect_git_commit(repo_path)

    resolved_host = host
    if resolved_host is None and detect_host:
        resolved_host = _detect_host()

    return RunManifest(
        run_id=run_id,
        config_hash=config_hash,
        created_at=created_at_str,
        schema_version=SCHEMA_VERSION,
        config=config_payload,
        universe=list(universe) if universe is not None else [],
        period={"start": period_start, "end": period_end},
        git_commit=resolved_git,
        host=resolved_host,
        trial_accounting=_to_jsonable(trial_accounting) if trial_accounting else {},
        extras=dict(extras) if extras else {},
    )


def manifest_to_dict(manifest: RunManifest) -> dict[str, Any]:
    return asdict(manifest)


def write_run_manifest_json(manifest: RunManifest, output_path: Path | str) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = manifest_to_dict(manifest)
    serialized = json.dumps(payload, sort_keys=True, indent=2)
    path.write_text(serialized + "\n", encoding="utf-8")
    return path
