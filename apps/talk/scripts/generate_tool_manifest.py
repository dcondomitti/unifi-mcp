#!/usr/bin/env python3
"""Generate the static tool manifest for unifi-talk-mcp.

Output: ``src/unifi_talk_mcp/tools_manifest.json``
"""

from __future__ import annotations

import sys
from pathlib import Path

from unifi_mcp_shared.manifest_generator import generate_and_write

if __name__ == "__main__":
    sys.exit(
        generate_and_write(
            project_root=Path(__file__).parent.parent,
            package="unifi_talk_mcp",
            tool_prefix="talk_",
            meta_prefix="talk",
            server_label="UniFi Talk",
            fallback_label="Talk",
            # Talk is not yet part of the cross-product support-bundle schema.
            support_bundle=False,
        )
    )
