#!/usr/bin/env python
# -*- coding: utf-8 -*-

import secrets
from datetime import datetime, timezone

# ============================================================
# SIH26028 - PROTOTYPE ROLE AUTHENTICATION
# ============================================================
#
# This is a DEMO-ONLY authentication layer for the SIH 2026
# prototype. Tokens are simple in-memory secrets and the demo
# passwords are stored in plain text in this source file on
# purpose. This is NOT production railway authentication and
# must not be presented as such.

ROLE_PASSENGER = "PASSENGER"
ROLE_CONTROL_ROOM = "CONTROL_ROOM"
ROLE_CO_PILOT = "CO_PILOT"

ALL_ROLES = (
    ROLE_PASSENGER,
    ROLE_CONTROL_ROOM,
    ROLE_CO_PILOT,
)

# Demo accounts - clearly labelled, prototype only.
DEMO_USERS = {
    "passenger123": {
        "password": "passenger123",
        "role": ROLE_PASSENGER,
        "display_name": "Passenger Demo",
    },
    "control123": {
        "password": "control123",
        "role": ROLE_CONTROL_ROOM,
        "display_name": "Control Room Demo",
    },
    "copilot123": {
        "password": "copilot123",
        "role": ROLE_CO_PILOT,
        "display_name": "Train Co-Pilot Demo",
    },
}


class AuthService:
    """Prototype role-based login for the SIH26028 demo.

    Tokens live only in process memory and are lost on restart.
    """

    def __init__(self):
        self._tokens = {}

    def login(self, username, password):
        """Validate demo credentials and issue a session token.

        Raises ValueError for unknown users or wrong passwords.
        """
        if username is None or password is None:
            raise ValueError("Username and password are required.")

        username = str(username).strip()
        password = str(password).strip()

        user = DEMO_USERS.get(username)

        if user is None or user["password"] != password:
            raise ValueError("Invalid username or password.")

        token = secrets.token_hex(16)

        self._tokens[token] = {
            "username": username,
            "role": user["role"],
            "display_name": user["display_name"],
            "issued_at": datetime.now(timezone.utc).isoformat(),
        }

        return {
            "token": token,
            "role": user["role"],
            "username": username,
            "display_name": user["display_name"],
            "issued_at": self._tokens[token]["issued_at"],
        }

    def verify_token(self, token):
        """Return the session dict for a valid token, else None."""
        if not token:
            return None

        return self._tokens.get(str(token).strip())

    def logout(self, token):
        """Invalidate a token."""
        if token:
            self._tokens.pop(str(token).strip(), None)

    def require_role(self, token, allowed_roles):
        """Return the session dict if the token role is allowed.

        Raises ValueError when the token is missing/invalid or the
        role is not permitted for the action.
        """
        session = self.verify_token(token)

        if session is None:
            raise ValueError("Missing or invalid session token.")

        if session["role"] not in allowed_roles:
            raise ValueError(
                "Not authorized for this action."
            )

        return session