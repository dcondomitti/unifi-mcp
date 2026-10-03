"""User tools for UniFi Talk MCP server.

Lists users with their Talk extension, numbers, ring groups and devices.
"""

import logging
from typing import Any, Dict

from mcp.types import ToolAnnotations

from unifi_core.talk.models.users import from_controller as user_from_controller
from unifi_talk_mcp.runtime import server, user_manager

logger = logging.getLogger(__name__)


@server.tool(
    name="talk_list_users",
    description=(
        "Lists users with their Talk extension, direct numbers, outbound caller ID, voicemail state, "
        "ring group membership, and assigned phones. The unique_id of each user is the user_id "
        "accepted by talk_list_calls."
    ),
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False),
    permission_category="user",
    permission_action="read",
    auth="local_only",
)
async def talk_list_users() -> Dict[str, Any]:
    """List Talk users."""
    logger.info("talk_list_users tool called")
    try:
        raw = await user_manager.list_users()
        users = [user_from_controller(u).model_dump(exclude_none=True) for u in raw]
        return {"success": True, "data": {"users": users, "count": len(users)}}
    except Exception as e:
        logger.error("Failed to list Talk users: %s", type(e).__name__, exc_info=True)
        return {"success": False, "error": f"Failed to list Talk users: {e}"}


logger.info("Talk user tools registered")
