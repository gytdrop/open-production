"""Audit recorder — appends one JSON line per gate decision to a JSONL file."""
from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path


class AuditRecorder:
    """Thread-safe recorder that writes gate decisions to a JSONL file.

    The file is truncated (or created fresh) on instantiation so each run
    starts with a clean audit trail.
    """

    def __init__(self, path: str = "audit_trail.jsonl") -> None:
        self.path = path
        self._lock = threading.Lock()
        # Truncate or create the file fresh on startup.
        Path(path).write_text("", encoding="utf-8")

    def record_gate_decision(
        self,
        gate_name: str,
        claim_id: str,
        decision_status: str,
        reason: str = "",
        evidence: dict | None = None,
    ) -> None:
        """Append one JSON line to self.path."""
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "gate_name": gate_name,
            "claim_id": claim_id,
            "decision_status": decision_status,
            "reason": reason,
            "evidence": evidence,
        }
        line = json.dumps(entry) + "\n"
        with self._lock:
            with open(self.path, "a", encoding="utf-8") as fh:
                fh.write(line)

    def entries(self) -> list[dict]:
        """Read all entries from the file. Return as list of dicts."""
        text = Path(self.path).read_text(encoding="utf-8")
        if not text.strip():
            return []
        return [json.loads(line) for line in text.splitlines() if line.strip()]
