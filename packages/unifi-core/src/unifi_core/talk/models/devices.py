"""Shared field model for Talk devices (read-only)."""

from __future__ import annotations

from typing import Any, Optional

from unifi_core.talk.models._base import TalkModel, as_dict, build, ro


class TalkDevice(TalkModel):
    """Canonical Talk phone/device model (read-only)."""

    mac: Optional[str] = ro("Device MAC address; the identifier used by talk_get_device")
    display_name: Optional[str] = ro("Device display name")
    model: Optional[str] = ro("Hardware model")
    status: Optional[str] = ro("Connection status reported by Talk")
    ip: Optional[str] = ro("Device IP address")
    version: Optional[str] = ro("Firmware version")
    serial_number: Optional[str] = ro("Hardware serial number")
    adopted: Optional[bool] = ro("Whether the device is adopted")
    sip_registered: Optional[bool] = ro("Whether the device is registered with the SIP server")
    ext: Optional[str] = ro("Assigned extension")
    user_id: Optional[str] = ro("unique_id of the assigned user")
    user_name: Optional[str] = ro("Name of the assigned user")
    uptime: Optional[int] = ro("Uptime in seconds")
    last_seen: Optional[str] = ro("Last time the device was seen")
    battery_level: Optional[Any] = ro("Battery level for cordless devices")
    update_available: Optional[str] = ro("Available firmware update, if any")


MUTABLE_FIELDS: frozenset[str] = frozenset()
READ_ONLY_FIELDS: frozenset[str] = frozenset(TalkDevice.model_fields)


def from_controller(raw: Any) -> TalkDevice:
    """Build a TalkDevice from a ``devices`` list entry."""
    data = as_dict(raw)
    return build(
        TalkDevice,
        {
            **data,
            "sip_registered": data.get("sip_reg"),
            "user_name": data.get("user"),
            "update_available": data.get("update_available") or None,
        },
    )
