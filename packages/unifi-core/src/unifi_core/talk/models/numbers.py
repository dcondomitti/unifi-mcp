"""Shared field model for Talk phone numbers (read-only)."""

from __future__ import annotations

from typing import Any, Optional

from unifi_core.talk.models._base import TalkModel, as_dict, build, ro


class TalkNumber(TalkModel):
    """Canonical Talk phone number model (read-only)."""

    did: Optional[str] = ro("Phone number (E.164)")
    plan: Optional[str] = ro("Subscription plan for the number")
    created_at: Optional[str] = ro("When the number was added")
    sms_capable: Optional[bool] = ro("Whether the number supports SMS")
    sms_enabled: Optional[bool] = ro("Whether SMS is enabled on the number")
    total_seconds: Optional[int] = ro("Total call seconds used on the number")
    sip_gateway_name: Optional[str] = ro("Third-party SIP gateway serving the number, if any")
    group_id: Optional[int] = ro("Ring group the number routes to")
    group_name: Optional[str] = ro("Name of the ring group the number routes to")
    smart_attendant_id: Optional[str] = ro("Smart attendant node the number routes to")
    smart_attendant_title: Optional[str] = ro("Title of the smart attendant the number routes to")


MUTABLE_FIELDS: frozenset[str] = frozenset()
READ_ONLY_FIELDS: frozenset[str] = frozenset(TalkNumber.model_fields)


def from_controller(raw: Any) -> TalkNumber:
    """Build a TalkNumber from a ``number/list`` entry."""
    data = as_dict(raw)
    group = as_dict(data.get("group_data")) or as_dict(data.get("group"))
    attendant = as_dict(data.get("smart_attendant"))
    return build(
        TalkNumber,
        {
            **data,
            "group_id": group.get("id"),
            "group_name": group.get("name"),
            "smart_attendant_id": attendant.get("id"),
            "smart_attendant_title": attendant.get("title"),
        },
    )
