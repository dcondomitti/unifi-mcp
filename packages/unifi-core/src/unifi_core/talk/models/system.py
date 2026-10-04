"""Shared field models for Talk system info and dashboard (read-only)."""

from __future__ import annotations

from typing import Any, Optional

from unifi_core.talk.models._base import TalkModel, as_dict, build, ro


class TalkSystemInfo(TalkModel):
    """Canonical Talk application info model (read-only)."""

    version: Optional[str] = ro("Talk application version")
    setup_complete: Optional[bool] = ro("Whether Talk setup has been completed")
    default_country_code: Optional[str] = ro("Default dialing country code")
    controller_region: Optional[str] = ro("Region the console is registered in")
    host_device_name: Optional[str] = ro("Name of the console hosting Talk")
    host_device_model: Optional[str] = ro("Model of the console hosting Talk")
    update_channel: Optional[str] = ro("Application update channel")
    call_recordings_available: Optional[bool] = ro("Whether call recording storage is available")
    has_switchboard: Optional[bool] = ro("Whether a smart attendant is configured")
    has_custom_gateways: Optional[bool] = ro("Whether third-party SIP gateways are configured")
    has_enabled_gateways: Optional[bool] = ro("Whether any SIP gateway is enabled")
    region_has_talk_service_support: Optional[bool] = ro("Whether the Talk calling service is offered in this region")


class TalkDashboard(TalkModel):
    """Canonical Talk dashboard summary model (read-only)."""

    console_name: Optional[str] = ro("Console display name")
    talk_service_enabled: Optional[bool] = ro("Whether the Talk calling service is enabled")
    uos_version: Optional[str] = ro("UniFi OS version")
    talk_version: Optional[str] = ro("Talk application version")
    system_startup_unix: Optional[int] = ro("Console startup time (Unix seconds)")
    device_count: Optional[int] = ro("Total Talk devices")
    online_devices_count: Optional[int] = ro("Online Talk devices")
    offline_devices_count: Optional[int] = ro("Offline Talk devices")


MUTABLE_FIELDS: frozenset[str] = frozenset()
READ_ONLY_FIELDS: frozenset[str] = frozenset(TalkSystemInfo.model_fields) | frozenset(TalkDashboard.model_fields)

_DASHBOARD_KEYS = {
    "console_name": "consoleName",
    "talk_service_enabled": "talkServiceEnabled",
    "uos_version": "uosVersion",
    "talk_version": "talkVersion",
    "system_startup_unix": "systemStartupUnix",
    "device_count": "deviceCount",
    "online_devices_count": "onlineDevicesCount",
    "offline_devices_count": "offlineDevicesCount",
}


def system_info_from_controller(raw: Any) -> TalkSystemInfo:
    """Build a TalkSystemInfo from the ``info`` response."""
    return build(TalkSystemInfo, as_dict(raw))


def dashboard_from_controller(raw: Any) -> TalkDashboard:
    """Build a TalkDashboard from the ``dashboard/consolidated_info`` response."""
    data = as_dict(raw)
    return build(TalkDashboard, {field: data.get(key) for field, key in _DASHBOARD_KEYS.items()})
