"""
Double-entry account ledger and transaction storage for the mock bank.
"""

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
    In-memory ledger storing balances and transaction history.
    """

    def __init__(self):
        self.transactions: List[LedgerEntry] = []

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
        entry = LedgerEntry(
            tx_id=tx_id,
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
        self.transactions.insert(0, entry)
        return entry

    def get_user_history(self, username: str) -> List[LedgerEntry]:
        return [
            tx for tx in self.transactions
            if tx.from_user == username or tx.to_user == username
        ]

    def get_all_history(self, limit: int = 100) -> List[LedgerEntry]:
        return self.transactions[:limit]

    def clear(self):
        self.transactions.clear()
