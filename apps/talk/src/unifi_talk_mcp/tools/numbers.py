"""Phone number tools for UniFi Talk MCP server."""

import logging
from typing import Any, Dict

from mcp.types import ToolAnnotations

from unifi_core.talk.models.numbers import from_controller as number_from_controller
from unifi_talk_mcp.runtime import number_manager, server

logger = logging.getLogger(__name__)


@server.tool(
    name="talk_list_numbers",
    description=(
        "Lists the phone numbers on the Talk account with plan, SMS capability, usage, "
        "and the ring group or smart attendant each number routes to."
    ),
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False),
    permission_category="number",
    permission_action="read",
    auth="local_only",
)
async def talk_list_numbers() -> Dict[str, Any]:
    """List Talk phone numbers."""
    logger.info("talk_list_numbers tool called")
    try:
        raw = await number_manager.list_numbers()
        numbers = [number_from_controller(n).model_dump(exclude_none=True) for n in raw]
        return {"success": True, "data": {"numbers": numbers, "count": len(numbers)}}
    except Exception as e:
        logger.error("Failed to list Talk numbers: %s", type(e).__name__, exc_info=True)
        return {"success": False, "error": f"Failed to list Talk numbers: {e}"}


@server.tool(
    name="talk_list_blocked_numbers",
    description=("Lists caller numbers that are blocked from reaching the Talk system."),
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False),
    permission_category="number",
    permission_action="read",
    auth="local_only",
)
async def talk_list_blocked_numbers() -> Dict[str, Any]:
    """List blocked caller numbers."""
    logger.info("talk_list_blocked_numbers tool called")
    try:
        blocked = await number_manager.list_blocked_numbers()
        return {"success": True, "data": {"blocked_numbers": blocked, "count": len(blocked)}}
    except Exception as e:
        logger.error("Failed to list Talk blocked numbers: %s", type(e).__name__, exc_info=True)
        return {"success": False, "error": f"Failed to list Talk blocked numbers: {e}"}


logger.info("Talk number tools registered")
