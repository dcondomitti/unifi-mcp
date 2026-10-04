"""Call-routing tools for UniFi Talk MCP server.

Ring groups, smart attendant, ring flows, call queues, parking lots, contacts
and call recording rules.
"""

import logging
from typing import Any, Awaitable, Callable, Dict, List

from mcp.types import ToolAnnotations

from unifi_core.redaction import redact_sensitive_fields
from unifi_core.talk.models.groups import from_controller as group_from_controller
from unifi_talk_mcp.runtime import callflow_manager, server, should_redact_sensitive_fields

logger = logging.getLogger(__name__)


async def _redacted_list(
    fetch: Callable[[], Awaitable[List[Dict[str, Any]]]], key: str, failure: str
) -> Dict[str, Any]:
    """Fetch a raw controller list and return it redacted under ``key``."""
    try:
        items = redact_sensitive_fields(await fetch(), redact_sensitive=should_redact_sensitive_fields())
        return {"success": True, "data": {key: items, "count": len(items)}}
    except Exception as e:
        logger.error("%s: %s", failure, type(e).__name__, exc_info=True)
        return {"success": False, "error": f"{failure}: {e}"}


@server.tool(
    name="talk_list_groups",
    description=(
        "Lists Talk ring groups with members, routed numbers and extensions, ring strategy, and the no-answer action."
    ),
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False),
    permission_category="callflow",
    permission_action="read",
    auth="local_only",
)
async def talk_list_groups() -> Dict[str, Any]:
    """List Talk ring groups."""
    logger.info("talk_list_groups tool called")
    try:
        raw = await callflow_manager.list_groups()
        groups = [group_from_controller(g).model_dump(exclude_none=True) for g in raw]
        return {"success": True, "data": {"groups": groups, "count": len(groups)}}
    except Exception as e:
        logger.error("Failed to list Talk groups: %s", type(e).__name__, exc_info=True)
        return {"success": False, "error": f"Failed to list Talk groups: {e}"}


@server.tool(
    name="talk_get_switchboard",
    description=(
        "Returns the smart attendant (auto-attendant/IVR) tree as nodes keyed by node id. Each node has a type, "
        "title or group name, extension, greeting settings, and childNodeIds linking to the next menu level."
    ),
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False),
    permission_category="callflow",
    permission_action="read",
    auth="local_only",
)
async def talk_get_switchboard() -> Dict[str, Any]:
    """Get the smart attendant tree."""
    logger.info("talk_get_switchboard tool called")
    try:
        raw = await callflow_manager.get_switchboard()
        nodes = redact_sensitive_fields(raw, redact_sensitive=should_redact_sensitive_fields())
        return {"success": True, "data": {"nodes": nodes, "count": len(nodes)}}
    except Exception as e:
        logger.error("Failed to get Talk switchboard: %s", type(e).__name__, exc_info=True)
        return {"success": False, "error": f"Failed to get Talk switchboard: {e}"}


@server.tool(
    name="talk_list_ring_flows",
    description=("Lists Talk ring flows (per-user call routing sequences)."),
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False),
    permission_category="callflow",
    permission_action="read",
    auth="local_only",
)
async def talk_list_ring_flows() -> Dict[str, Any]:
    """List Talk ring flows."""
    logger.info("talk_list_ring_flows tool called")
    return await _redacted_list(callflow_manager.list_ring_flows, "ring_flows", "Failed to list Talk ring flows")


@server.tool(
    name="talk_list_call_queues",
    description=("Lists Talk call-center queues."),
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False),
    permission_category="callflow",
    permission_action="read",
    auth="local_only",
)
async def talk_list_call_queues() -> Dict[str, Any]:
    """List Talk call queues."""
    logger.info("talk_list_call_queues tool called")
    return await _redacted_list(callflow_manager.list_queues, "queues", "Failed to list Talk call queues")


@server.tool(
    name="talk_list_parking_lots",
    description=("Lists Talk call parking lots."),
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False),
    permission_category="callflow",
    permission_action="read",
    auth="local_only",
)
async def talk_list_parking_lots() -> Dict[str, Any]:
    """List Talk parking lots."""
    logger.info("talk_list_parking_lots tool called")
    return await _redacted_list(callflow_manager.list_parking_lots, "parking_lots", "Failed to list Talk parking lots")


@server.tool(
    name="talk_list_contacts",
    description=("Lists shared contacts stored in Talk."),
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False),
    permission_category="callflow",
    permission_action="read",
    auth="local_only",
)
async def talk_list_contacts() -> Dict[str, Any]:
    """List Talk contacts."""
    logger.info("talk_list_contacts tool called")
    return await _redacted_list(callflow_manager.list_contacts, "contacts", "Failed to list Talk contacts")


@server.tool(
    name="talk_list_recording_rules",
    description=(
        "Lists Talk call recording rules: direction, numbers covered, internal-call recording, and the recording announcement."
    ),
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False),
    permission_category="callflow",
    permission_action="read",
    auth="local_only",
)
async def talk_list_recording_rules() -> Dict[str, Any]:
    """List Talk call recording rules."""
    logger.info("talk_list_recording_rules tool called")
    return await _redacted_list(
        callflow_manager.list_recording_rules, "recording_rules", "Failed to list Talk call recording rules"
    )


logger.info("Talk call-routing tools registered")
