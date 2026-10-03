"""System-level reads for UniFi Talk.

Paths discovered via browser inspection (all relative to ``/proxy/talk/api/``):
- ``info`` -- application version, host console, feature availability
- ``dashboard/consolidated_info`` -- console name, service state, device counts
- ``dashboard/service_health?presetTime=1D`` -- health score time series
- ``setting/config`` -- voicemail, recording, transcription and SIP settings
- ``billing/usage`` -- minutes, SMS and transcription usage counters
"""

from __future__ import annotations

from typing import Any, Dict, List

from unifi_core.talk.managers.connection_manager import TalkConnectionManager


class SystemManager:
    """Reads system-level data from the Talk application."""

    def __init__(self, connection_manager: TalkConnectionManager) -> None:
        self._cm = connection_manager

    async def get_info(self) -> Dict[str, Any]:
        """Return Talk application info (version, host console, capabilities)."""
        data = await self._cm.request("GET", "info", operation="Get Talk system info")
        return data if isinstance(data, dict) else {}

    async def get_dashboard(self) -> Dict[str, Any]:
        """Return the consolidated dashboard summary (service state, device counts)."""
        data = await self._cm.request("GET", "dashboard/consolidated_info", operation="Get Talk dashboard")
        return data if isinstance(data, dict) else {}

    async def get_service_health(self, preset_time: str = "1D") -> List[Dict[str, Any]]:
        """Return health-score buckets for the given preset window."""
        data = await self._cm.request(
            "GET",
            "dashboard/service_health",
            operation="Get Talk service health",
            params={"presetTime": preset_time},
        )
        buckets = data.get("health_data") if isinstance(data, dict) else None
        return buckets if isinstance(buckets, list) else []

    async def get_settings(self) -> Dict[str, Any]:
        """Return global Talk settings (voicemail, recording, transcription, SIP)."""
        data = await self._cm.request("GET", "setting/config", operation="Get Talk settings")
        return data if isinstance(data, dict) else {}

    async def get_usage(self) -> Dict[str, Any]:
        """Return usage counters (minutes, SMS, CNAM, transcriptions, softphone)."""
        data = await self._cm.request("GET", "billing/usage", operation="Get Talk usage")
        return data if isinstance(data, dict) else {}
