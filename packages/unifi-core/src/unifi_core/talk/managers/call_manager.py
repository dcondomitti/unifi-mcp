"""Call log and voicemail reads for UniFi Talk.

Paths (relative to ``/proxy/talk/api/``):
- ``call_log?page=`` -- every call on the console, newest first, 50 per zero-based page;
  each record embeds its event timeline and, when present, voicemail metadata
- ``call_log/user/{user_id}?limit=&offset=`` -- one user's calls, newest first
- ``call_log/flow/{call_uuid}`` -- event timeline for one call
- ``voicemail/data/{call_uuid}`` -- voicemail metadata for a call that went to voicemail
- ``transcript/by_call_uuid?call_uuid=&transcript_source=call`` -- call transcript

A voicemail shares its ``uuid`` with the call that produced it, so voicemails
are reached from call-log entries.
"""

from __future__ import annotations

from typing import Any, Dict, List

from unifi_core.exceptions import UniFiNotFoundError
from unifi_core.talk.managers.connection_manager import TalkConnectionManager

MAX_CALL_PAGE = 100
ALL_CALLS_PAGE_SIZE = 50


class CallManager:
    """Reads call history, call flows, voicemail and transcripts."""

    def __init__(self, connection_manager: TalkConnectionManager) -> None:
        self._cm = connection_manager

    async def list_all_calls(self, page: int = 0) -> Dict[str, Any]:
        """Return ``{"calls": [...], "total_count": int | None}`` for one console-wide page."""
        if page < 0:
            raise ValueError("page must be 0 or greater")
        data = await self._cm.request("GET", "call_log", operation="List all Talk calls", params={"page": page})
        if not isinstance(data, dict):
            return {"calls": [], "total_count": None}
        records = data.get("records")
        calls = [c for c in records if isinstance(c, dict)] if isinstance(records, list) else []
        try:
            total = int(data.get("total_count"))
        except (TypeError, ValueError):
            total = None
        return {"calls": calls, "total_count": total}

    async def list_calls(self, user_id: str, limit: int = 25, offset: int = 0) -> Dict[str, Any]:
        """Return ``{"calls": [...], "total_count": int}`` for one user."""
        if not user_id:
            raise ValueError("user_id is required")
        if not 1 <= limit <= MAX_CALL_PAGE:
            raise ValueError(f"limit must be between 1 and {MAX_CALL_PAGE}")
        if offset < 0:
            raise ValueError("offset must be 0 or greater")
        data = await self._cm.request(
            "GET",
            f"call_log/user/{user_id}",
            operation="List Talk calls",
            params={"limit": limit, "offset": offset},
        )
        if not isinstance(data, dict):
            return {"calls": [], "total_count": 0}
        calls = data.get("calls")
        calls = [c for c in calls if isinstance(c, dict)] if isinstance(calls, list) else []
        total = data.get("total_count")
        return {"calls": calls, "total_count": total if isinstance(total, int) else len(calls)}

    async def get_call_flow(self, call_id: str) -> List[Dict[str, Any]]:
        """Return the ordered event timeline for one call."""
        data = await self._cm.request("GET", f"call_log/flow/{call_id}", operation="Get Talk call flow")
        return [e for e in data if isinstance(e, dict)] if isinstance(data, list) else []

    async def get_voicemail(self, call_id: str) -> Dict[str, Any]:
        """Return voicemail metadata for a call that went to voicemail."""
        data = await self._cm.request("GET", f"voicemail/data/{call_id}", operation="Get Talk voicemail")
        if not isinstance(data, dict) or not data:
            raise UniFiNotFoundError("talk_voicemail", call_id)
        return data

    async def get_transcript(self, call_id: str) -> Any:
        """Return the transcript for a call, or ``None`` when none exists."""
        return await self._cm.request(
            "GET",
            "transcript/by_call_uuid",
            operation="Get Talk call transcript",
            params={"call_uuid": call_id, "transcript_source": "call"},
        )
