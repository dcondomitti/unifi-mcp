"""Call-routing reads for UniFi Talk.

Paths (relative to ``/proxy/talk/api/``):
- ``group_list`` -- ring groups with members, numbers and no-answer handling
- ``switchboard`` -- smart attendant tree, normalized as nodes keyed by id
- ``ring_flow`` -- per-user ring flows
- ``call_center/queue`` -- call queues
- ``parking_lots`` -- call parking lots
- ``contacts`` -- shared contacts
- ``call_recording_rule`` -- call recording rules
"""

from __future__ import annotations

from typing import Any, Dict, List

from unifi_core.talk.managers.connection_manager import TalkConnectionManager


def _dict_list(data: Any) -> List[Dict[str, Any]]:
    return [item for item in data if isinstance(item, dict)] if isinstance(data, list) else []


class CallFlowManager:
    """Reads call-routing configuration from the Talk application."""

    def __init__(self, connection_manager: TalkConnectionManager) -> None:
        self._cm = connection_manager

    async def list_groups(self) -> List[Dict[str, Any]]:
        """Return ring groups."""
        return _dict_list(await self._cm.request("GET", "group_list", operation="List Talk groups"))

    async def get_switchboard(self) -> Dict[str, Any]:
        """Return smart attendant nodes keyed by node id."""
        data = await self._cm.request("GET", "switchboard", operation="Get Talk switchboard")
        try:
            nodes = data["entities"]["nodes"]["byId"]
        except (KeyError, TypeError):
            return {}
        return nodes if isinstance(nodes, dict) else {}

    async def list_ring_flows(self) -> List[Dict[str, Any]]:
        """Return ring flows."""
        return _dict_list(await self._cm.request("GET", "ring_flow", operation="List Talk ring flows"))

    async def list_queues(self) -> List[Dict[str, Any]]:
        """Return call queues."""
        return _dict_list(await self._cm.request("GET", "call_center/queue", operation="List Talk call queues"))

    async def list_parking_lots(self) -> List[Dict[str, Any]]:
        """Return call parking lots."""
        return _dict_list(await self._cm.request("GET", "parking_lots", operation="List Talk parking lots"))

    async def list_contacts(self) -> List[Dict[str, Any]]:
        """Return shared contacts."""
        return _dict_list(await self._cm.request("GET", "contacts", operation="List Talk contacts"))

    async def list_recording_rules(self) -> List[Dict[str, Any]]:
        """Return call recording rules."""
        return _dict_list(
            await self._cm.request("GET", "call_recording_rule", operation="List Talk call recording rules")
        )
