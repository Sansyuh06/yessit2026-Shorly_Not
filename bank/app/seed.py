"""
Seed data specification for ShorlyNot Mock Bank.
Normative specification from PRD §8.3 and §B9.
"""

from typing import Dict, Any


class BankUser:
    def __init__(self, username: str, password: str, role: str, starting_balance: float, key_id: str):
        self.username = username
        self.password = password
        self.role = role  # customer | attacker | soc
        self.balance = starting_balance
        self.key_id = key_id


def get_default_seed_users() -> Dict[str, BankUser]:
    """
    User    Password   Role       Starting Balance (INR)
    alice   alice123   customer   50,000
    bob     bob123     customer   20,000
    carol   carol123   customer   10,000
    eve     eve123     attacker    1,000
    ops     ops123     soc             0
    """
    return {
        "alice": BankUser("alice", "alice123", "customer", 50000.0, "alice-key-1"),
        "bob": BankUser("bob", "bob123", "customer", 20000.0, "bob-key-1"),
        "carol": BankUser("carol", "carol123", "customer", 10000.0, "carol-key-1"),
        "eve": BankUser("eve", "eve123", "attacker", 1000.0, "eve-key-1"),
        "ops": BankUser("ops", "ops123", "soc", 0.0, "ops-key-1"),
    }
