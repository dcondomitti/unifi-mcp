"""Shared field models for Talk calls, call-flow events and voicemail (read-only)."""

from __future__ import annotations

from typing import Any, Dict, Optional

from unifi_core.talk.models._base import TalkModel, as_dict, build, ro


class TalkCall(TalkModel):
    """Canonical Talk call-log entry model (read-only)."""

    uuid: Optional[str] = ro("Call identifier; pass as call_id to the call flow, voicemail and transcript tools")
    direction: Optional[str] = ro("Call direction: 'in' or 'out'")
    status: Optional[str] = ro("Call outcome reported by Talk (e.g. 'accepted', 'cancelled')")
    time: Optional[str] = ro("Call start time")
    duration: Optional[int] = ro("Call duration in seconds")
    from_number: Optional[str] = ro("Caller number or extension")
    to_number: Optional[str] = ro("Dialed number or extension")
    from_id: Optional[str] = ro("unique_id of the calling user, when internal")
    to_id: Optional[str] = ro("unique_id of the called user, when internal")
    from_mac: Optional[str] = ro("MAC of the device that placed the call")
    answered_by_mac: Optional[str] = ro("MAC of the device that answered the call")
    recording: Optional[bool] = ro("Whether a recording exists for the call")
    quality_score: Optional[int] = ro("Call quality score")
    is_video_call: Optional[bool] = ro("Whether the call was a video call")
    is_intercom_call: Optional[bool] = ro("Whether the call was an intercom call")
    from_caller_name: Optional[str] = ro("Caller name, when known")
    answered_by: Optional[str] = ro("Name or extension of whoever answered")
    country: Optional[str] = ro("Country of the external party")
    to_smart_attendant_title: Optional[str] = ro("Smart attendant the call was routed to")
    has_voicemail: Optional[bool] = ro("Whether the call left a voicemail (console-wide call log only)")


class TalkCallEvent(TalkModel):
    """One event in a call's flow timeline (read-only)."""

    time: Optional[str] = ro("Event time")
    event: Optional[str] = ro(
        "Event type (e.g. call_started, call_accepted, call_sent_to_voicemail, vm_msg_recorded, call_hangup)"
    )
    event_uuid: Optional[str] = ro("Event identifier")
    event_data: Dict[str, Any] = ro("Event-specific details", default={})


class TalkVoicemail(TalkModel):
    """Canonical Talk voicemail metadata model (read-only)."""

    uuid: Optional[str] = ro("Voicemail identifier; equal to the uuid of the call that left it")
    received_at: Optional[str] = ro("When the voicemail was received")
    read_at: Optional[str] = ro("When the voicemail was first listened to")
    duration: Optional[str] = ro("Voicemail length as reported by Talk")
    vm_left_for_ext: Optional[str] = ro("Extension the voicemail was left for")
    vm_receiver_uuid: Optional[str] = ro("unique_id of the user who received the voicemail")
    file_path: Optional[str] = ro("Controller-side path of the audio file")


MUTABLE_FIELDS: frozenset[str] = frozenset()
READ_ONLY_FIELDS: frozenset[str] = (
    frozenset(TalkCall.model_fields) | frozenset(TalkCallEvent.model_fields) | frozenset(TalkVoicemail.model_fields)
)


def call_from_controller(raw: Any) -> TalkCall:
    """Build a TalkCall from a ``call_log/user/{id}`` entry."""
    data = as_dict(raw)
    # Only the console-wide log carries vm_data; leave has_voicemail unset elsewhere.
    has_voicemail = bool(data["vm_data"]) if "vm_data" in data else None
    return build(
        TalkCall,
        {**data, "from_number": data.get("from"), "to_number": data.get("to"), "has_voicemail": has_voicemail},
    )


def call_event_from_controller(raw: Any) -> TalkCallEvent:
    """Build a TalkCallEvent from a ``call_log/flow/{id}`` entry."""
    data = as_dict(raw)
    return build(TalkCallEvent, {**data, "event_data": as_dict(data.get("event_data"))})


def voicemail_from_controller(raw: Any) -> TalkVoicemail:
    """Build a TalkVoicemail from a ``voicemail/data/{id}`` response."""
    data = as_dict(raw)
    duration = data.get("duration")
    return build(TalkVoicemail, {**data, "duration": None if duration is None else str(duration)})
