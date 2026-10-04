"""User reads for UniFi Talk.

Paths (relative to ``/proxy/talk/api/``):
- ``users`` -- console users joined with their Talk extension, numbers and devices
"""

from __future__ import annotations

from typing import Any, Dict, List

from unifi_core.exceptions import UniFiNotFoundError
from unifi_core.talk.managers.connection_manager import TalkConnectionManager


class UserManager:
    """Reads user data from the Talk application."""

    def __init__(self, connection_manager: TalkConnectionManager) -> None:
        self._cm = connection_manager

    async def list_users(self) -> List[Dict[str, Any]]:
        """Return all users visible to Talk."""
        data = await self._cm.request("GET", "users", operation="List Talk users")
        return [u for u in data if isinstance(u, dict)] if isinstance(data, list) else []

    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """Return one user by ``unique_id``."""
        for user in await self.list_users():
            if user.get("unique_id") == user_id:
                return user
        raise UniFiNotFoundError("talk_user", user_id)
