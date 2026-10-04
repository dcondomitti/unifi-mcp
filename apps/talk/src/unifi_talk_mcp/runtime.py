# ruff: noqa: E402
from __future__ import annotations

"""Shared runtime objects for the UniFi-Talk MCP server.

This module is the *single* source of truth for global singletons such as the
FastMCP server instance, loaded configuration, and all manager helpers.

Downstream code (tool modules, tests, etc.) should import these via::

    from unifi_talk_mcp.runtime import server, config, device_manager

Lazy factories (`get_*`) are provided so unit tests can substitute fakes by
monkey-patching before the first call.

IMPORTANT: The server's `tool` decorator is wrapped here (not in main.py) to
ensure that tool modules can be imported directly (for testing, etc.) without
errors from unrecognized decorator kwargs like `permission_category`.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from mcp.server.transport_security import TransportSecuritySettings

from unifi_mcp_shared.metadata import PROJECT_WEBSITE_URL, configure_mcp_server_metadata
from unifi_mcp_shared.response_policy import resolve_mcp_content_mode, should_redact_response_sensitive_fields
from unifi_mcp_shared.server import UniFiMCPServer, resolve_allowed_hosts
from unifi_talk_mcp.bootstrap import load_config, logger

_TOOLS_MANIFEST_PATH = Path(__file__).resolve().parent / "tools_manifest.json"
from unifi_core.talk.managers.call_manager import CallManager
from unifi_core.talk.managers.callflow_manager import CallFlowManager
from unifi_core.talk.managers.connection_manager import TalkConnectionManager
from unifi_core.talk.managers.device_manager import DeviceManager
from unifi_core.talk.managers.number_manager import NumberManager
from unifi_core.talk.managers.system_manager import SystemManager
from unifi_core.talk.managers.user_manager import UserManager
from unifi_talk_mcp.tool_index import TOOL_REGISTRY

# ---------------------------------------------------------------------------
# Core singletons
# ---------------------------------------------------------------------------


@lru_cache
def get_config():
    """Load and cache configuration."""
    return load_config()


def _create_permissioned_tool_wrapper(original_tool_decorator):
    """Wrap the FastMCP tool decorator to handle permission kwargs.

    This wrapper strips `permission_category` and `permission_action` kwargs
    before passing to the original FastMCP decorator. This allows tool modules
    to be imported directly (for testing, etc.) without errors.

    The actual permission checking is done in main.py's permissioned_tool,
    which replaces this wrapper at startup. This wrapper just ensures imports
    don't fail when tools have permission kwargs.
    """

    def wrapper(*args, **kwargs):
        # Strip permission-related kwargs that FastMCP doesn't understand
        kwargs.pop("permission_category", None)
        kwargs.pop("permission_action", None)
        kwargs.pop("auth", None)
        return original_tool_decorator(*args, **kwargs)

    return wrapper


@lru_cache
def get_server() -> UniFiMCPServer:
    """Create the FastMCP server instance exactly once."""
    # The operator owns the public allowlist. Deployments such as Docker Compose
    # can add required internal service names without overriding that setting.
    allowed_hosts = resolve_allowed_hosts(
        os.getenv("UNIFI_MCP_ALLOWED_HOSTS"),
        override_hosts=(
            os.getenv("UNIFI_MCP_COMPOSE_ALLOWED_HOSTS_OVERRIDE")
            if os.getenv("UNIFI_MCP_COMPOSE_ALLOWED_HOSTS_OVERRIDE_SET") == "true"
            else None
        ),
        internal_hosts=os.getenv("UNIFI_MCP_INTERNAL_ALLOWED_HOSTS"),
    )

    # Allow disabling DNS rebinding protection entirely (default: enabled)
    # Set to "false" for Kubernetes/proxy deployments where allowed_hosts is insufficient
    enable_dns_rebinding = os.getenv("UNIFI_MCP_ENABLE_DNS_REBINDING_PROTECTION", "true").lower() == "true"

    transport_security = TransportSecuritySettings(
        allowed_hosts=allowed_hosts,
        enable_dns_rebinding_protection=enable_dns_rebinding,
    )

    logger.debug(
        "Configuring FastMCP with allowed_hosts: %s, dns_rebinding_protection: %s",
        allowed_hosts,
        enable_dns_rebinding,
    )

    server = UniFiMCPServer(
        name="unifi-talk-mcp",
        debug=True,
        website_url=PROJECT_WEBSITE_URL,
        transport_security=transport_security,
        tools_manifest_path=_TOOLS_MANIFEST_PATH,
        mcp_content_mode=resolve_mcp_content_mode("talk", config=get_config()),
    )
    configure_mcp_server_metadata(server, package_name="unifi-talk-mcp")

    # Wrap the tool decorator to handle permission kwargs gracefully.
    # This ensures tool modules can be imported directly without errors.
    # main.py will replace this with the full permissioned_tool implementation.
    from unifi_mcp_shared.protocol import create_mcp_tool_adapter

    # server._original_tool must be set to the adapter (not raw server.tool),
    # because setup_permissioned_tool reads server._original_tool and uses it
    # as the bottom of the decorator chain.
    server._original_tool = create_mcp_tool_adapter(server.tool)
    server.tool = _create_permissioned_tool_wrapper(server._original_tool)

    return server


# ---------------------------------------------------------------------------
# Manager factories ---------------------------------------------------------
# ---------------------------------------------------------------------------


@lru_cache
def get_connection_manager() -> TalkConnectionManager:
    cfg = get_config().unifi
    return TalkConnectionManager(
        host=cfg.host,
        username=cfg.username,
        password=cfg.password,
        port=int(cfg.port),
        verify_ssl=str(cfg.verify_ssl).lower() in ("true", "1", "yes"),
    )


@lru_cache
def get_system_manager() -> SystemManager:
    return SystemManager(get_connection_manager())


@lru_cache
def get_device_manager() -> DeviceManager:
    return DeviceManager(get_connection_manager())


@lru_cache
def get_user_manager() -> UserManager:
    return UserManager(get_connection_manager())


@lru_cache
def get_number_manager() -> NumberManager:
    return NumberManager(get_connection_manager())


@lru_cache
def get_call_manager() -> CallManager:
    return CallManager(get_connection_manager())


@lru_cache
def get_callflow_manager() -> CallFlowManager:
    return CallFlowManager(get_connection_manager())


@lru_cache
def get_tool_registry() -> dict[str, Any]:
    """Return the global tool registry for runtime access."""
    return TOOL_REGISTRY


# ---------------------------------------------------------------------------
# Shorthand aliases (import-time singletons) --------------------------------
# ---------------------------------------------------------------------------

config = get_config()
server = get_server()
connection_manager = get_connection_manager()
system_manager = get_system_manager()
device_manager = get_device_manager()
user_manager = get_user_manager()
number_manager = get_number_manager()
call_manager = get_call_manager()
callflow_manager = get_callflow_manager()
tool_registry = get_tool_registry()


def should_redact_sensitive_fields() -> bool:
    """Whether Talk MCP responses should redact sensitive fields.

    Policy-resolved per call (env → config) so the surface-specific and global
    ``UNIFI_*REDACT_SENSITIVE_FIELDS`` overrides both take effect. Binds the
    ``"talk"`` prefix + config in one place for the tool modules.
    """
    return should_redact_response_sensitive_fields("talk", config)


logger.debug("runtime.py: shared singletons initialised")
