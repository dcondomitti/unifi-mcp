# ruff: noqa: E402
from __future__ import annotations

"""Bootstrap utilities for the UniFi-Talk MCP server.

This module consolidates:
- environment loading
- logging configuration
- configuration loading / validation

Importing it early guarantees deterministic side-effects (env + logging) and
exposes a `load_config()` helper that the rest of the codebase can share.
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from omegaconf import OmegaConf

from unifi_core.config import load_yaml_config  # noqa: F401 -- re-export for convenience
from unifi_core.config import setup_logging as _shared_setup_logging

# ---------------------------------------------------------------------------
# Environment & logging
# ---------------------------------------------------------------------------
# Use only the launcher-supplied environment. Project .env files are never loaded:
# they must not select credential destinations or weaken permissions/redaction.
# Operators can explicitly load a trusted env file in their launcher.
from unifi_mcp_shared.bootstrap import load_process_env

load_process_env()


DEFAULT_LOG_LEVEL = os.getenv("UNIFI_MCP_LOG_LEVEL", "INFO").upper()


def setup_logging(level: str | None = None) -> logging.Logger:
    """Configure root logger once and return the project logger."""
    return _shared_setup_logging("unifi-talk-mcp", level=level or DEFAULT_LOG_LEVEL)


logger = setup_logging()


# ---------------------------------------------------------------------------
# Domain config dataclasses  -------------------------------------------------
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class TalkSettings:
    host: str
    username: str
    password: str
    port: int = 443
    verify_ssl: bool = False

    @classmethod
    def from_omegaconf(cls, cfg: Any) -> "TalkSettings":
        """Create from an OmegaConf config object."""
        return cls(
            host=str(cfg.host),
            username=str(cfg.username),
            password=str(cfg.password),
            port=int(cfg.get("port", 443)),
            verify_ssl=bool(cfg.get("verify_ssl", False)),
        )


# ---------------------------------------------------------------------------
# Config loading  -----------------------------------------------------------
# ---------------------------------------------------------------------------


def load_config(path_override: str | Path | None = None) -> OmegaConf:
    """Load YAML config with environment variable substitution."""
    from unifi_mcp_shared.bootstrap import load_server_config

    return load_server_config(
        package_name="unifi_talk_mcp.config",
        env_prefix="TALK",
        keys=("host", "username", "password", "port", "verify_ssl"),
        logger=logger,
    )


# ---------------------------------------------------------------------------
# Tool registration mode
# ---------------------------------------------------------------------------

from unifi_mcp_shared.bootstrap import validate_registration_mode

UNIFI_TOOL_REGISTRATION_MODE = validate_registration_mode(logger)
