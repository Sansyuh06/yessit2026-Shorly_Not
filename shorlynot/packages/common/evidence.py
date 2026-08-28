"""Immutable evidence chain with SHA-256 hash chaining.

Every major system action creates an EvidenceRecord. Records are linked
by previous_hash to form a tamper-evident chain. The first record uses
'GENESIS' as its previous_hash.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from packages.common.enums import ExecutionMode


class EvidenceChain:
    """Append-only hash-chained evidence log."""

    GENESIS = "GENESIS"

    def __init__(self) -> None:
        self._records: list[dict[str, Any]] = []
        self._last_hash: str = self.GENESIS

    @property
    def records(self) -> list[dict[str, Any]]:
        return list(self._records)

    @property
    def last_hash(self) -> str:
        return self._last_hash

    @property
    def length(self) -> int:
        return len(self._records)

    def append(
        self,
        event_type: str,
        execution_mode: ExecutionMode,
        source: str,
        payload: dict[str, Any],
        timestamp: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """Create and append a new evidence record.

        Returns the complete record dict including computed hashes.
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        record_id = str(uuid.uuid4())
        payload_hash = self._hash_payload(payload)

        # Build canonical record (without record_hash)
        canonical = {
            "id": record_id,
            "event_type": event_type,
            "timestamp": timestamp.isoformat(),
            "execution_mode": execution_mode.value,
            "source": source,
            "payload_hash": payload_hash,
            "previous_hash": self._last_hash,
        }

        record_hash = self._hash_record(canonical)

        record = {**canonical, "record_hash": record_hash}
        self._records.append(record)
        self._last_hash = record_hash

        return record

    def verify(self) -> tuple[bool, Optional[int]]:
        """Verify the complete chain integrity.

        Returns (valid, first_failed_index). If valid, first_failed_index is None.
        """
        expected_previous = self.GENESIS

        for i, record in enumerate(self._records):
            # Check previous_hash linkage
            if record["previous_hash"] != expected_previous:
                return False, i

            # Recompute record_hash
            canonical = {k: v for k, v in record.items() if k != "record_hash"}
            expected_hash = self._hash_record(canonical)
            if record["record_hash"] != expected_hash:
                return False, i

            expected_previous = record["record_hash"]

        return True, None

    @staticmethod
    def _hash_payload(payload: dict[str, Any]) -> str:
        """SHA-256 of canonical JSON payload."""
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def _hash_record(canonical_record: dict[str, Any]) -> str:
        """SHA-256 of canonical record (excluding record_hash field)."""
        canonical = json.dumps(
            canonical_record, sort_keys=True, separators=(",", ":"), default=str
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_list(self) -> list[dict[str, Any]]:
        """Export all records for serialization."""
        return list(self._records)

    @classmethod
    def from_list(cls, records: list[dict[str, Any]]) -> "EvidenceChain":
        """Reconstruct chain from stored records."""
        chain = cls()
        chain._records = list(records)
        if records:
            chain._last_hash = records[-1]["record_hash"]
        return chain
