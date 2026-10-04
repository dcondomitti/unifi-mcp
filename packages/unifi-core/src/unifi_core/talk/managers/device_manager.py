"""Phone and device reads for UniFi Talk.

Paths (relative to ``/proxy/talk/api/``):
- ``devices`` -- all adopted and third-party phones

Talk has no get-by-id read endpoint for devices; :meth:`get_device` filters
the list by MAC address.
"""

from __future__ import annotations

from typing import Any, Dict, List

from unifi_core.exceptions import UniFiNotFoundError
from unifi_core.talk.managers.connection_manager import TalkConnectionManager


def _normalize_mac(mac: str) -> str:
    return "".join(c for c in mac.lower() if c in "0123456789abcdef")


class DeviceManager:
    """Reads phone/device data from the Talk application."""

    def __init__(self, connection_manager: TalkConnectionManager) -> None:
        self._cm = connection_manager

    async def list_devices(self) -> List[Dict[str, Any]]:
        """Return all Talk devices."""
        data = await self._cm.request("GET", "devices", operation="List Talk devices")
        return [d for d in data if isinstance(d, dict)] if isinstance(data, list) else []

    async def get_device(self, mac: str) -> Dict[str, Any]:
        """Return one Talk device by MAC address (any separator style)."""
        wanted = _normalize_mac(mac)
        if len(wanted) != 12:
            raise ValueError("mac must be a 12-digit hexadecimal MAC address")
        for device in await self.list_devices():
            if _normalize_mac(str(device.get("mac", ""))) == wanted:
                return device
        raise UniFiNotFoundError("talk_device", mac)
