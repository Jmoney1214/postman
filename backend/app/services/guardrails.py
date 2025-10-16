from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict


@dataclass
class SessionState:
    is_age_verified: bool = False


class Guardrails:
    def __init__(self) -> None:
        self._sessions: Dict[str, SessionState] = {}

    def verify_age(self, session_id: str, dob_iso: str) -> bool:
        # Basic 21+ check from YYYY-MM-DD
        try:
            dob = datetime.strptime(dob_iso, "%Y-%m-%d").date()
        except Exception:
            return False
        today = date.today()
        years = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        is_21 = years >= 21
        if is_21:
            state = self._sessions.setdefault(session_id, SessionState())
            state.is_age_verified = True
        return is_21

    def is_verified(self, session_id: str) -> bool:
        return self._sessions.get(session_id, SessionState()).is_age_verified

    def is_intoxication_signaled(self, text: str) -> bool:
        lowered = text.lower()
        keywords = [
            "drunk",
            "wasted",
            "hammered",
            "blackout",
            "tipsy",
            "too drunk",
            "intoxicated",
        ]
        return any(k in lowered for k in keywords)


guardrails = Guardrails()
