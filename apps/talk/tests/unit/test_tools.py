"""Tool-layer tests for the UniFi Talk MCP server."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, patch

import pytest

from unifi_core.exceptions import UniFiConnectionError, UniFiNotFoundError

os.environ.setdefault("UNIFI_TALK_HOST", "127.0.0.1")
os.environ.setdefault("UNIFI_TALK_USERNAME", "test")
os.environ.setdefault("UNIFI_TALK_PASSWORD", "test")

REDACTED = "***REDACTED***"


async def test_get_system_info_projects_safe_fields():
    with patch("unifi_talk_mcp.tools.system.system_manager") as manager:
        manager.get_info = AsyncMock(return_value={"version": "5.4.4", "host_device_serial": "SERIAL"})
        from unifi_talk_mcp.tools.system import talk_get_system_info

        result = await talk_get_system_info()
    assert result == {"success": True, "data": {"version": "5.4.4"}}


async def test_get_dashboard_and_health_and_usage():
    with patch("unifi_talk_mcp.tools.system.system_manager") as manager:
        manager.get_dashboard = AsyncMock(return_value={"consoleName": "HQ", "deviceCount": 2})
        manager.get_service_health = AsyncMock(return_value=[{"health_score": 100}])
        manager.get_usage = AsyncMock(return_value={"minutes": {"standard": 3}})
        from unifi_talk_mcp.tools.system import talk_get_dashboard, talk_get_service_health, talk_get_usage

        assert await talk_get_dashboard() == {"success": True, "data": {"console_name": "HQ", "device_count": 2}}
        assert await talk_get_service_health(preset_time="1D") == {
            "success": True,
            "data": {"health": [{"health_score": 100}], "count": 1},
        }
        manager.get_service_health.assert_awaited_once_with("1D")
        assert await talk_get_usage() == {"success": True, "data": {"minutes": {"standard": 3}}}


async def test_get_settings_redacts_secret_fields_by_default():
    raw = {"voicemail_enabled": True, "sip_password": "hunter2", "nested": {"api_key": "k"}}
    with patch("unifi_talk_mcp.tools.system.system_manager") as manager:
        manager.get_settings = AsyncMock(return_value=raw)
        from unifi_talk_mcp.tools.system import talk_get_settings

        result = await talk_get_settings()
    assert result["success"] is True
    assert result["data"]["voicemail_enabled"] is True
    assert result["data"]["sip_password"] == REDACTED
    assert result["data"]["nested"]["api_key"] == REDACTED


async def test_system_tool_error_names_operation():
    with patch("unifi_talk_mcp.tools.system.system_manager") as manager:
        manager.get_info = AsyncMock(side_effect=UniFiConnectionError("Get Talk system info failed: HTTP 500"))
        from unifi_talk_mcp.tools.system import talk_get_system_info

        result = await talk_get_system_info()
    assert result == {
        "success": False,
        "error": "Failed to get Talk system info: Get Talk system info failed: HTTP 500",
    }


async def test_list_devices_never_returns_sip_password():
    raw = [{"mac": "aabbccddeeff", "model": "UTP", "sip_reg": True, "additional_config": {"sip_password": "hunter2"}}]
    with patch("unifi_talk_mcp.tools.devices.device_manager") as manager:
        manager.list_devices = AsyncMock(return_value=raw)
        from unifi_talk_mcp.tools.devices import talk_list_devices

        result = await talk_list_devices()
    assert result == {
        "success": True,
        "data": {"devices": [{"mac": "aabbccddeeff", "model": "UTP", "sip_registered": True}], "count": 1},
    }


async def test_get_device_not_found_and_invalid_mac():
    with patch("unifi_talk_mcp.tools.devices.device_manager") as manager:
        from unifi_talk_mcp.tools.devices import talk_get_device

        manager.get_device = AsyncMock(side_effect=UniFiNotFoundError("talk_device", "001122334455"))
        assert await talk_get_device(mac="001122334455") == {
            "success": False,
            "error": "talk_device '001122334455' not found",
        }
        manager.get_device = AsyncMock(side_effect=ValueError("mac must be a 12-digit hexadecimal MAC address"))
        result = await talk_get_device(mac="nope")
        assert result["success"] is False
        assert "12-digit" in result["error"]


async def test_list_users_projects_talk_fields():
    raw = [{"unique_id": "u1", "full_name": "Jane Doe", "ext": "100", "sip_password": "hunter2", "scopes": ["a"]}]
    with patch("unifi_talk_mcp.tools.users.user_manager") as manager:
        manager.list_users = AsyncMock(return_value=raw)
        from unifi_talk_mcp.tools.users import talk_list_users

        result = await talk_list_users()
    assert result == {
        "success": True,
        "data": {
            "users": [{"unique_id": "u1", "full_name": "Jane Doe", "ext": "100", "ring_groups": [], "devices": []}],
            "count": 1,
        },
    }


async def test_number_tools():
    with patch("unifi_talk_mcp.tools.numbers.number_manager") as manager:
        manager.list_numbers = AsyncMock(return_value=[{"did": "+15551234567", "group_data": {"id": 4, "name": "S"}}])
        manager.list_blocked_numbers = AsyncMock(return_value=[])
        from unifi_talk_mcp.tools.numbers import talk_list_blocked_numbers, talk_list_numbers

        assert await talk_list_numbers() == {
            "success": True,
            "data": {"numbers": [{"did": "+15551234567", "group_id": 4, "group_name": "S"}], "count": 1},
        }
        assert await talk_list_blocked_numbers() == {"success": True, "data": {"blocked_numbers": [], "count": 0}}


async def test_list_calls_passes_pagination_and_reports_total():
    page = {"calls": [{"uuid": "c1", "from": "100", "to": "101", "direction": "out"}], "total_count": 47}
    with patch("unifi_talk_mcp.tools.calls.call_manager") as manager:
        manager.list_calls = AsyncMock(return_value=page)
        from unifi_talk_mcp.tools.calls import talk_list_calls

        result = await talk_list_calls(user_id="u1", limit=5, offset=10)
    manager.list_calls.assert_awaited_once_with("u1", limit=5, offset=10)
    assert result == {
        "success": True,
        "data": {
            "calls": [{"uuid": "c1", "direction": "out", "from_number": "100", "to_number": "101"}],
            "count": 1,
            "total_count": 47,
            "offset": 10,
        },
    }


async def test_list_calls_validation_error_is_returned_not_raised():
    with patch("unifi_talk_mcp.tools.calls.call_manager") as manager:
        manager.list_calls = AsyncMock(side_effect=ValueError("user_id is required"))
        from unifi_talk_mcp.tools.calls import talk_list_calls

        assert await talk_list_calls(user_id="") == {"success": False, "error": "user_id is required"}


async def test_call_flow_voicemail_and_transcript():
    with patch("unifi_talk_mcp.tools.calls.call_manager") as manager:
        manager.get_call_flow = AsyncMock(return_value=[{"event": "call_sent_to_voicemail", "time": "t"}])
        manager.get_voicemail = AsyncMock(return_value={"uuid": "c1", "duration": 12})
        manager.get_transcript = AsyncMock(return_value=None)
        from unifi_talk_mcp.tools.calls import talk_get_call_flow, talk_get_call_transcript, talk_get_voicemail

        flow = await talk_get_call_flow(call_id="c1")
        assert flow["data"]["events"] == [{"time": "t", "event": "call_sent_to_voicemail", "event_data": {}}]
        assert await talk_get_voicemail(call_id="c1") == {"success": True, "data": {"uuid": "c1", "duration": "12"}}
        assert await talk_get_call_transcript(call_id="c1") == {
            "success": True,
            "data": {"call_id": "c1", "transcript": None},
        }

        manager.get_voicemail = AsyncMock(side_effect=UniFiNotFoundError("talk_voicemail", "c2"))
        assert await talk_get_voicemail(call_id="c2") == {"success": False, "error": "talk_voicemail 'c2' not found"}


async def test_callflow_tools():
    with patch("unifi_talk_mcp.tools.callflow.callflow_manager") as manager:
        manager.list_groups = AsyncMock(return_value=[{"id": 4, "name": "Sales", "member_list": ["u1"]}])
        manager.get_switchboard = AsyncMock(return_value={"swb_4": {"type": "sa", "sip_password": "hunter2"}})
        manager.list_contacts = AsyncMock(return_value=[{"name": "Vendor", "api_token": "t"}])
        manager.list_ring_flows = AsyncMock(side_effect=UniFiConnectionError("List Talk ring flows failed: HTTP 500"))
        from unifi_talk_mcp.tools.callflow import (
            talk_get_switchboard,
            talk_list_contacts,
            talk_list_groups,
            talk_list_ring_flows,
        )

        groups = await talk_list_groups()
        assert groups["data"]["count"] == 1
        assert groups["data"]["groups"][0]["member_list"] == ["u1"]

        board = await talk_get_switchboard()
        assert board["data"]["nodes"]["swb_4"] == {"type": "sa", "sip_password": REDACTED}

        contacts = await talk_list_contacts()
        assert contacts["data"] == {"contacts": [{"name": "Vendor", "api_token": REDACTED}], "count": 1}

        failed = await talk_list_ring_flows()
        assert failed == {
            "success": False,
            "error": "Failed to list Talk ring flows: List Talk ring flows failed: HTTP 500",
        }


@pytest.mark.parametrize(
    ("tool", "method", "key"),
    [
        ("talk_list_call_queues", "list_queues", "queues"),
        ("talk_list_parking_lots", "list_parking_lots", "parking_lots"),
        ("talk_list_recording_rules", "list_recording_rules", "recording_rules"),
    ],
)
async def test_passthrough_list_tools(tool, method, key):
    with patch("unifi_talk_mcp.tools.callflow.callflow_manager") as manager:
        setattr(manager, method, AsyncMock(return_value=[{"id": 1}]))
        import unifi_talk_mcp.tools.callflow as module

        result = await getattr(module, tool)()
    assert result == {"success": True, "data": {key: [{"id": 1}], "count": 1}}
