"""Device tools for UniFi Talk MCP server.

Lists and inspects Talk phones and third-party SIP devices.
"""

import logging
from typing import Annotated, Any, Dict

from mcp.types import ToolAnnotations
from pydantic import Field

from unifi_core.exceptions import UniFiNotFoundError
from unifi_core.talk.models.devices import from_controller as device_from_controller
from unifi_talk_mcp.runtime import device_manager, server

logger = logging.getLogger(__name__)


@server.tool(
    name="talk_list_devices",
    description=(
        "Lists all Talk phones and third-party SIP devices with name, model, connection status, firmware, "
        "extension, SIP registration state, and assigned user."
    ),
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False),
    permission_category="device",
    permission_action="read",
    auth="local_only",
)
async def talk_list_devices() -> Dict[str, Any]:
    """List all Talk devices."""
    logger.info("talk_list_devices tool called")
    try:
        raw = await device_manager.list_devices()
        devices = [device_from_controller(d).model_dump(exclude_none=True) for d in raw]
        return {"success": True, "data": {"devices": devices, "count": len(devices)}}
    except Exception as e:
        logger.error("Failed to list Talk devices: %s", type(e).__name__, exc_info=True)
        return {"success": False, "error": f"Failed to list Talk devices: {e}"}


@server.tool(
    name="talk_get_device",
    description=(
        "Returns one Talk device by MAC address: name, model, status, IP, firmware, extension, "
        "SIP registration state, and assigned user."
    ),
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False),
    permission_category="device",
    permission_action="read",
    auth="local_only",
)
async def talk_get_device(
    mac: Annotated[
        str, Field(description="Device MAC address as returned by talk_list_devices (any separator style).")
    ],
) -> Dict[str, Any]:
    """Get one Talk device by MAC address."""
    logger.info("talk_get_device tool called")
    try:
        raw = await device_manager.get_device(mac)
        return {"success": True, "data": device_from_controller(raw).model_dump(exclude_none=True)}
    except (UniFiNotFoundError, ValueError) as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error("Failed to get Talk device: %s", type(e).__name__, exc_info=True)
        return {"success": False, "error": f"Failed to get Talk device: {e}"}


logger.info("Talk device tools registered")
