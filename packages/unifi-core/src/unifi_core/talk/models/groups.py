"""Shared field model for Talk ring groups (read-only)."""

from __future__ import annotations

from typing import Any, List, Optional

from unifi_core.talk.models._base import TalkModel, as_dict, build, ro


class TalkGroup(TalkModel):
    """Canonical Talk ring group model (read-only)."""

    id: Optional[int] = ro("Group numeric id")
    uuid: Optional[str] = ro("Group UUID")
    name: Optional[str] = ro("Group name")
    group_type: Optional[str] = ro("Group type (e.g. 'ring_group')")
    call_handling: Optional[str] = ro("How members are rung (e.g. 'simultaneous')")
    no_answer_action: Optional[str] = ro("What happens when nobody answers")
    simultaneous_ring_timeout: Optional[int] = ro("Seconds to ring members before the no-answer action")
    member_list: List[Any] = ro("unique_ids of member users", default=[])
    did_list: List[Any] = ro("Phone numbers routed to the group", default=[])
    ext_list: List[Any] = ro("Extensions routed to the group", default=[])
    vm_receiver_uuids: List[Any] = ro("unique_ids of users who receive the group's voicemail", default=[])


MUTABLE_FIELDS: frozenset[str] = frozenset()
READ_ONLY_FIELDS: frozenset[str] = frozenset(TalkGroup.model_fields)


def from_controller(raw: Any) -> TalkGroup:
    """Build a TalkGroup from a ``group_list`` entry."""
    data = as_dict(raw)
    lists = {
        key: data.get(key) if isinstance(data.get(key), list) else []
        for key in ("member_list", "did_list", "ext_list", "vm_receiver_uuids")
    }
    return build(TalkGroup, {**data, **lists})
