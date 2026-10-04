"""System tools for UniFi Talk MCP server.

Application info, dashboard summary, service health, global settings and usage.
"""

import logging
from typing import Annotated, Any, Dict

from mcp.types import ToolAnnotations
from pydantic import Field

from unifi_core.redaction import redact_sensitive_fields
from unifi_core.talk.models.system import dashboard_from_controller, system_info_from_controller
from unifi_talk_mcp.runtime import server, should_redact_sensitive_fields, system_manager

logger = logging.getLogger(__name__)


@server.tool(
    name="talk_get_system_info",
    description=(
        "Returns the UniFi Talk application version, host console model, region, and feature availability "
        "(call recording storage, smart attendant, SIP gateways). Use for a basic capability check."
    ),
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False),
    permission_category="system",
    permission_action="read",
    auth="local_only",
)
async def talk_get_system_info() -> Dict[str, Any]:
    """Get Talk application info."""
    logger.info("talk_get_system_info tool called")
    try:
        raw = await system_manager.get_info()
        return {"success": True, "data": system_info_from_controller(raw).model_dump(exclude_none=True)}
    except Exception as e:
        logger.error("Failed to get Talk system info: %s", type(e).__name__, exc_info=True)
        return {"success": False, "error": f"Failed to get Talk system info: {e}"}


@server.tool(
    name="talk_get_dashboard",
    description=(
        "Returns the Talk dashboard summary: console name, whether the calling service is enabled, "
        "Talk and UniFi OS versions, and total/online/offline phone counts."
    ),
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False),
    permission_category="system",
    permission_action="read",
    auth="local_only",
)
async def talk_get_dashboard() -> Dict[str, Any]:
    """Get the Talk dashboard summary."""
    logger.info("talk_get_dashboard tool called")
    try:
        raw = await system_manager.get_dashboard()
        return {"success": True, "data": dashboard_from_controller(raw).model_dump(exclude_none=True)}
    except Exception as e:
        logger.error("Failed to get Talk dashboard: %s", type(e).__name__, exc_info=True)
        return {"success": False, "error": f"Failed to get Talk dashboard: {e}"}


@server.tool(
    name="talk_get_service_health",
    description=(
        "Returns Talk service health as a time series of buckets, each with a start/end timestamp, "
        "a health score, and any health events. Use to spot calling-service degradation."
    ),
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False),
    permission_category="system",
    permission_action="read",
    auth="local_only",
)
async def talk_get_service_health(
    preset_time: Annotated[
        str,
        Field(description="Time window preset as used by the Talk dashboard. '1D' (last day) is the verified value."),
    ] = "1D",
) -> Dict[str, Any]:
    """Get Talk service health buckets."""
    logger.info("talk_get_service_health tool called")
    try:
        buckets = await system_manager.get_service_health(preset_time)
        return {"success": True, "data": {"health": buckets, "count": len(buckets)}}
    except Exception as e:
        logger.error("Failed to get Talk service health: %s", type(e).__name__, exc_info=True)
        return {"success": False, "error": f"Failed to get Talk service health: {e}"}


@server.tool(
    name="talk_get_settings",
    description=(
        "Returns global Talk settings: voicemail (enabled, timeout, email/Slack/Teams delivery), call recording, "
        "AI transcription, caller-ID passthrough, audio codecs, SIP/NAT options, and emergency address status."
    ),
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False),
    permission_category="system",
    permission_action="read",
    auth="local_only",
)
async def talk_get_settings() -> Dict[str, Any]:
    """Get global Talk settings."""
    logger.info("talk_get_settings tool called")
    try:
        raw = await system_manager.get_settings()
        settings = redact_sensitive_fields(raw, redact_sensitive=should_redact_sensitive_fields())
        return {"success": True, "data": settings}
    except Exception as e:
        logger.error("Failed to get Talk settings: %s", type(e).__name__, exc_info=True)
        return {"success": False, "error": f"Failed to get Talk settings: {e}"}


@server.tool(
    name="talk_get_usage",
    description=(
        "Returns Talk usage counters for the current billing period: call minutes, SMS, CNAM lookups, "
        "transcriptions, and softphone usage."
    ),
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False),
    permission_category="system",
    permission_action="read",
    auth="local_only",
)
async def talk_get_usage() -> Dict[str, Any]:
    """Get Talk usage counters."""
    logger.info("talk_get_usage tool called")
    try:
        usage = await system_manager.get_usage()
        return {"success": True, "data": usage}
    except Exception as e:
        logger.error("Failed to get Talk usage: %s", type(e).__name__, exc_info=True)
        return {"success": False, "error": f"Failed to get Talk usage: {e}"}


logger.info("Talk system tools registered")
