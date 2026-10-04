"""Shared field model for Talk users (read-only)."""

from __future__ import annotations

from typing import Any, List, Optional

from unifi_core.talk.models._base import TalkModel, as_dict, build, ro


class TalkUserDevice(TalkModel):
    """A device assigned to a Talk user."""

    mac: Optional[str] = ro("Device MAC address")
    model: Optional[str] = ro("Hardware model")
    display_name: Optional[str] = ro("Device display name")
    status: Optional[str] = ro("Connection status")


class TalkUserGroup(TalkModel):
    """A ring group a Talk user belongs to."""

    id: Optional[int] = ro("Group numeric id")
    uuid: Optional[str] = ro("Group UUID")
    name: Optional[str] = ro("Group name")


class TalkUser(TalkModel):
    """Canonical Talk user model (read-only)."""

    unique_id: Optional[str] = ro("User identifier; pass as user_id to talk_list_calls")
    full_name: Optional[str] = ro("Full name")
    email: Optional[str] = ro("Email address")
    status: Optional[str] = ro("Account status")
    ext: Optional[str] = ro("Assigned extension")
    did: Optional[str] = ro("Primary direct number")
    did_list: Optional[List[Any]] = ro("All direct numbers assigned to the user")
    outbound_caller_id: Optional[Any] = ro("Outbound caller ID setting: a number, or a numeric reference to one")
    voicemail_enabled: Optional[bool] = ro("Whether voicemail is enabled for the user")
    has_active_calls: Optional[bool] = ro("Whether the user is on a call right now")
    accept_queue_calls: Optional[bool] = ro("Whether the user accepts call-queue calls")
    ring_groups: List[TalkUserGroup] = ro("Ring groups the user belongs to", default=[])
    devices: List[TalkUserDevice] = ro("Devices assigned to the user", default=[])


MUTABLE_FIELDS: frozenset[str] = frozenset()
READ_ONLY_FIELDS: frozenset[str] = frozenset(TalkUser.model_fields)


def _dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def from_controller(raw: Any) -> TalkUser:
    """Build a TalkUser from a ``users`` list entry."""
    data = as_dict(raw)
    return build(
        TalkUser,
        {
            **data,
            "email": data.get("email") or data.get("user_email") or None,
            "status": data.get("user_status") or data.get("status"),
            "ring_groups": _dicts(data.get("ring_groups")),
            "devices": _dicts(data.get("devices")),
        },
    )
