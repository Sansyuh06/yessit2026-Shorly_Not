"""
Double-entry account ledger and transaction storage for the mock bank.
Supports SQLite database persistence with automatic table initialization.
"""

import os
import sqlite3
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class LedgerEntry(BaseModel):
    tx_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    from_user: str
    to_user: str
    amount: float
    currency: str = "INR"
    status: str = "COMMITTED"  # COMMITTED | REJECTED | BLOCKED
    mismatch_rate: float = 0.0
    tau: float = 0.2097
    threat_label: str = "OK"
    stage_s: int = 0
    details: str = ""


class BankLedger:
    """
    Bank ledger with SQLite persistence and fast in-memory querying.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.environ.get("BANK_DB_PATH", os.path.join(os.path.dirname(__file__), "..", "bank_ledger.db"))
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ledger_transactions (
                        tx_id TEXT PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        from_user TEXT NOT NULL,
                        to_user TEXT NOT NULL,
                        amount REAL NOT NULL,
                        currency TEXT NOT NULL,
                        status TEXT NOT NULL,
                        mismatch_rate REAL NOT NULL,
                        tau REAL NOT NULL,
                        threat_label TEXT NOT NULL,
                        stage_s INTEGER NOT NULL,
                        details TEXT
                    )
                """)
                conn.commit()
        except Exception:
            pass

    def record_transaction(
        self,
        tx_id: str,
        from_user: str,
        to_user: str,
        amount: float,
        status: str,
        mismatch_rate: float,
        tau: float,
        threat_label: str,
        stage_s: int,
        details: str = ""
    ) -> LedgerEntry:
        timestamp = datetime.now(timezone.utc).isoformat()
        entry = LedgerEntry(
            tx_id=tx_id,
            timestamp=timestamp,
            from_user=from_user,
            to_user=to_user,
            amount=amount,
            currency="INR",
            status=status,
            mismatch_rate=round(mismatch_rate, 4),
            tau=round(tau, 4),
            threat_label=threat_label,
            stage_s=stage_s,
            details=details
        )

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO ledger_transactions 
                    (tx_id, timestamp, from_user, to_user, amount, currency, status, mismatch_rate, tau, threat_label, stage_s, details)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry.tx_id, entry.timestamp, entry.from_user, entry.to_user,
                    entry.amount, entry.currency, entry.status, entry.mismatch_rate,
                    entry.tau, entry.threat_label, entry.stage_s, entry.details
                ))
                conn.commit()
        except Exception:
            pass

        return entry

    def get_user_history(self, username: str) -> List[LedgerEntry]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM ledger_transactions 
                    WHERE from_user = ? OR to_user = ?
                    ORDER BY timestamp DESC
                """, (username, username))
                rows = cursor.fetchall()
                return [LedgerEntry(**dict(row)) for row in rows]
        except Exception:
            return []

    def get_all_history(self, limit: int = 100) -> List[LedgerEntry]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM ledger_transactions 
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))
                rows = cursor.fetchall()
                return [LedgerEntry(**dict(row)) for row in rows]
        except Exception:
            return []

    def clear(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM ledger_transactions")
                conn.commit()
        except Exception:
            pass
