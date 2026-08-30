"""
Session-based authentication and user management for the mock bank.
"""

from typing import Optional, Dict
from fastapi import Request
from bank.app.seed import BankUser, get_default_seed_users


class BankAuthManager:
    """
    Manages user sessions and authentication.
    """

    def __init__(self):
        self.users: Dict[str, BankUser] = get_default_seed_users()
        self.sessions: Dict[str, str] = {}  # session_token -> username

    def authenticate(self, username: str, password: str) -> Optional[BankUser]:
        user = self.users.get(username)
        if user and user.password == password:
            return user
        return None

    def create_session(self, username: str) -> str:
        import uuid
        token = f"sess-{uuid.uuid4().hex}"
        self.sessions[token] = username
        return token

    def get_current_user(self, request: Request) -> Optional[BankUser]:
        token = request.cookies.get("session_token")
        if not token or token not in self.sessions:
            return None
        username = self.sessions[token]
        return self.users.get(username)

    def revoke_session(self, request: Request):
        token = request.cookies.get("session_token")
        if token and token in self.sessions:
            del self.sessions[token]

    def reset_users(self):
        self.users = get_default_seed_users()
        self.sessions.clear()
