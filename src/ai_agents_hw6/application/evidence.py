from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from ai_agents_hw6.application.events import atomic_write_json


def build_evidence_manifest(
    *,
    config_path: str | Path,
    event_log_path: str,
    report_path: str,
) -> dict[str, Any]:
    config_bytes = Path(config_path).read_bytes()
    return {
        "phase": 9,
        "config_path": str(config_path),
        "config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "git_commit": _read_git_commit(),
        "event_log_path": event_log_path,
        "replay_command": f"python main.py --config {config_path} --replay-events {event_log_path}",
        "report_path": report_path,
        "verification_commands": [
            "python -m unittest discover -s tests -p test_*.py",
            "python -m compileall -q main.py src tests",
            "python main.py --mode internal --config config.json --engine-only --quiet",
        ],
    }


def write_evidence_manifest(path: str | Path, manifest: dict[str, Any]) -> None:
    atomic_write_json(path, manifest)


def _read_git_commit() -> str | None:
    head_path = Path(".git/HEAD")
    if not head_path.exists():
        return None
    head = head_path.read_text(encoding="utf-8").strip()
    if not head.startswith("ref: "):
        return head
    ref_path = Path(".git") / head.removeprefix("ref: ")
    if ref_path.exists():
        return ref_path.read_text(encoding="utf-8").strip()
    packed_refs = Path(".git/packed-refs")
    if packed_refs.exists():
        for line in packed_refs.read_text(encoding="utf-8").splitlines():
            if line and not line.startswith("#") and line.endswith(head.removeprefix("ref: ")):
                return line.split(" ", 1)[0]
    return None
