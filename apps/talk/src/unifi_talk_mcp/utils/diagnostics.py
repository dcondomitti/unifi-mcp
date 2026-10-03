"""Tool and API diagnostics — re-exported from shared package."""

from unifi_core.diagnostics import (
    diagnostics_enabled,
    init_diagnostics,
    log_api_request,
    log_tool_call,
    wrap_tool,
)


# Initialize with talk server's config provider
def _get_config():
    from unifi_talk_mcp.runtime import config

    return config


init_diagnostics(
    config_provider=_get_config,
    logger_name="unifi-talk-mcp.diagnostics",
)

__all__ = ["diagnostics_enabled", "init_diagnostics", "log_api_request", "log_tool_call", "wrap_tool"]
