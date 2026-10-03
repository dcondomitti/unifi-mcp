"""Smoke tests for the UniFi Talk MCP server scaffold."""

import json
from pathlib import Path

EXPECTED_TOOLS = {
    "talk_get_system_info": "system",
    "talk_get_dashboard": "system",
    "talk_get_service_health": "system",
    "talk_get_settings": "system",
    "talk_get_usage": "system",
    "talk_list_devices": "devices",
    "talk_get_device": "devices",
    "talk_list_users": "users",
    "talk_list_numbers": "numbers",
    "talk_list_blocked_numbers": "numbers",
    "talk_list_calls": "calls",
    "talk_get_call_flow": "calls",
    "talk_get_voicemail": "calls",
    "talk_get_call_transcript": "calls",
    "talk_list_groups": "callflow",
    "talk_get_switchboard": "callflow",
    "talk_list_ring_flows": "callflow",
    "talk_list_call_queues": "callflow",
    "talk_list_parking_lots": "callflow",
    "talk_list_contacts": "callflow",
    "talk_list_recording_rules": "callflow",
}

MANIFEST = Path(__file__).parents[2] / "src" / "unifi_talk_mcp" / "tools_manifest.json"


def test_package_importable():
    import unifi_talk_mcp

    assert unifi_talk_mcp.__doc__ is not None


def test_managers_importable():
    from unifi_core.talk.managers.call_manager import CallManager
    from unifi_core.talk.managers.callflow_manager import CallFlowManager
    from unifi_core.talk.managers.connection_manager import TalkConnectionManager
    from unifi_core.talk.managers.device_manager import DeviceManager
    from unifi_core.talk.managers.number_manager import NumberManager
    from unifi_core.talk.managers.system_manager import SystemManager
    from unifi_core.talk.managers.user_manager import UserManager

    cm = TalkConnectionManager(host="test", username="test", password="test")
    for manager in (CallManager, CallFlowManager, DeviceManager, NumberManager, SystemManager, UserManager):
        assert manager(cm) is not None


def test_tool_module_map_matches_expected_tools():
    from unifi_talk_mcp.categories import TALK_CATEGORY_MAP, TOOL_MODULE_MAP

    assert {name: module.rsplit(".", 1)[-1] for name, module in TOOL_MODULE_MAP.items()} == EXPECTED_TOOLS
    assert set(TALK_CATEGORY_MAP.values()) == set(EXPECTED_TOOLS.values())


def test_manifest_tools_are_read_only_and_closed_world():
    manifest = json.loads(MANIFEST.read_text())
    tools = {tool["name"]: tool for tool in manifest["tools"]}
    assert set(EXPECTED_TOOLS) <= set(tools)
    # Talk is not part of the cross-product support-bundle schema yet.
    assert "talk_get_support_bundle" not in tools
    for name in EXPECTED_TOOLS:
        annotations = tools[name]["annotations"]
        assert annotations["readOnlyHint"] is True, name
        assert annotations["openWorldHint"] is False, name


def test_policy_gates_only_cover_reads():
    from unifi_talk_mcp.categories import TALK_CATEGORY_MAP, policy_gates

    gates = policy_gates()
    assert {action for _, action in gates} <= {"read"}
    assert {category for category, _ in gates} <= set(TALK_CATEGORY_MAP)
