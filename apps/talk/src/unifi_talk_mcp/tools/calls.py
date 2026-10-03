"""Call tools for UniFi Talk MCP server.

Call log, call-flow timelines, voicemail metadata and transcripts. The call log
is per-user; a voicemail shares its uuid with the call that left it.
"""

import logging
from typing import Annotated, Any, Dict

from mcp.types import ToolAnnotations
from pydantic import Field

from unifi_core.exceptions import UniFiNotFoundError
from unifi_core.talk.managers.call_manager import MAX_CALL_PAGE
from unifi_core.talk.models.calls import (
    call_event_from_controller,
    call_from_controller,
    voicemail_from_controller,
)
from unifi_talk_mcp.runtime import call_manager, server

logger = logging.getLogger(__name__)


@server.tool(
    name="talk_list_calls",
    description=(
        "Lists one user's call history, newest first, with direction, status, time, duration, numbers, "
        "recording flag, and quality score. Talk has no console-wide call log: call this once per user "
        "(user_id is the unique_id from talk_list_users). Paginate with limit/offset; total_count is the "
        "user's full call count."
    ),
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False),
    permission_category="call",
    permission_action="read",
    auth="local_only",
)
async def talk_list_calls(
    user_id: Annotated[str, Field(description="User unique_id as returned by talk_list_users.")],
    limit: Annotated[int, Field(description=f"Calls per page (1-{MAX_CALL_PAGE}).", ge=1, le=MAX_CALL_PAGE)] = 25,
    offset: Annotated[int, Field(description="Number of calls to skip, for pagination.", ge=0)] = 0,
) -> Dict[str, Any]:
    """List one user's call history."""
    logger.info("talk_list_calls tool called")
    try:
        page = await call_manager.list_calls(user_id, limit=limit, offset=offset)
        calls = [call_from_controller(c).model_dump(exclude_none=True) for c in page["calls"]]
        return {
            "success": True,
            "data": {
                "calls": calls,
                "count": len(calls),
                "total_count": page["total_count"],
                "offset": offset,
            },
        }
    except (UniFiNotFoundError, ValueError) as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error("Failed to list Talk calls: %s", type(e).__name__, exc_info=True)
        return {"success": False, "error": f"Failed to list Talk calls: {e}"}


@server.tool(
    name="talk_get_call_flow",
    description=(
        "Returns the ordered event timeline for one call (started, endpoints tried, accepted, "
        "sent to voicemail, voicemail recorded, hangup). A call_sent_to_voicemail or vm_msg_recorded "
        "event means talk_get_voicemail will return data for the same call_id."
    ),
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False),
    permission_category="call",
    permission_action="read",
    auth="local_only",
)
async def talk_get_call_flow(
    call_id: Annotated[str, Field(description="Call uuid as returned by talk_list_calls.")],
) -> Dict[str, Any]:
    """Get the event timeline for one call."""
    logger.info("talk_get_call_flow tool called")
    try:
        raw = await call_manager.get_call_flow(call_id)
        events = [call_event_from_controller(e).model_dump(exclude_none=True) for e in raw]
        return {"success": True, "data": {"events": events, "count": len(events)}}
    except (UniFiNotFoundError, ValueError) as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error("Failed to get Talk call flow: %s", type(e).__name__, exc_info=True)
        return {"success": False, "error": f"Failed to get Talk call flow: {e}"}


@server.tool(
    name="talk_get_voicemail",
    description=(
        "Returns voicemail metadata for a call that went to voicemail: received and read times, duration, "
        "the extension it was left for, and the receiving user. Returns an error for calls with no voicemail. "
        "Audio is not returned."
    ),
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False),
    permission_category="call",
    permission_action="read",
    auth="local_only",
)
async def talk_get_voicemail(
    call_id: Annotated[str, Field(description="Call uuid as returned by talk_list_calls.")],
) -> Dict[str, Any]:
    """Get voicemail metadata for a call."""
    logger.info("talk_get_voicemail tool called")
    try:
        raw = await call_manager.get_voicemail(call_id)
        return {"success": True, "data": voicemail_from_controller(raw).model_dump(exclude_none=True)}
    except (UniFiNotFoundError, ValueError) as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error("Failed to get Talk voicemail: %s", type(e).__name__, exc_info=True)
        return {"success": False, "error": f"Failed to get Talk voicemail: {e}"}


@server.tool(
    name="talk_get_call_transcript",
    description=(
        "Returns the AI transcript for a call when call transcription is enabled and a transcript exists; "
        "otherwise transcript is null."
    ),
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False),
    permission_category="call",
    permission_action="read",
    auth="local_only",
)
async def talk_get_call_transcript(
    call_id: Annotated[str, Field(description="Call uuid as returned by talk_list_calls.")],
) -> Dict[str, Any]:
    """Get the transcript for a call."""
    logger.info("talk_get_call_transcript tool called")
    try:
        transcript = await call_manager.get_transcript(call_id)
        return {"success": True, "data": {"call_id": call_id, "transcript": transcript}}
    except (UniFiNotFoundError, ValueError) as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error("Failed to get Talk call transcript: %s", type(e).__name__, exc_info=True)
        return {"success": False, "error": f"Failed to get Talk call transcript: {e}"}


logger.info("Talk call tools registered")
