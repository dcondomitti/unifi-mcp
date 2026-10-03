"""Phone number reads for UniFi Talk.

Paths (relative to ``/proxy/talk/api/``):
- ``number/list`` -- purchased/ported numbers with their group or smart attendant
- ``number/blocked`` -- blocked caller numbers
"""

from __future__ import annotations

from typing import Any, Dict, List

from unifi_core.talk.managers.connection_manager import TalkConnectionManager


class NumberManager:
    """Reads phone number data from the Talk application."""

    def __init__(self, connection_manager: TalkConnectionManager) -> None:
        self._cm = connection_manager

    async def list_numbers(self) -> List[Dict[str, Any]]:
        """Return all phone numbers on the Talk account."""
        data = await self._cm.request("GET", "number/list", operation="List Talk numbers")
        return [n for n in data if isinstance(n, dict)] if isinstance(data, list) else []

    async def list_blocked_numbers(self) -> List[Any]:
        """Return blocked caller numbers."""
        data = await self._cm.request("GET", "number/blocked", operation="List Talk blocked numbers")
        return data if isinstance(data, list) else []
