"""Pytest configuration for unifi-talk-mcp tests."""

import sys
from pathlib import Path

# Add the talk app's src directory to path so unifi_talk_mcp is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
