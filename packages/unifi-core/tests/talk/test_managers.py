"""Tests for the Talk domain managers."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from unifi_core.exceptions import UniFiNotFoundError
from unifi_core.talk.managers.call_manager import MAX_CALL_PAGE, CallManager
from unifi_core.talk.managers.callflow_manager import CallFlowManager
from unifi_core.talk.managers.connection_manager import TalkConnectionManager
from unifi_core.talk.managers.device_manager import DeviceManager
from unifi_core.talk.managers.number_manager import NumberManager
from unifi_core.talk.managers.system_manager import SystemManager
from unifi_core.talk.managers.user_manager import UserManager


@pytest.fixture
def cm():
    manager = TalkConnectionManager(host="192.168.1.1", username="admin", password="secret")
    manager.request = AsyncMock()
    return manager


async def test_system_manager_paths_and_shapes(cm):
    mgr = SystemManager(cm)
    cm.request.return_value = {"version": "5.4.4"}
    assert await mgr.get_info() == {"version": "5.4.4"}
    assert cm.request.await_args.args == ("GET", "info")

    cm.request.return_value = {"health_data": [{"health_score": 100}]}
    assert await mgr.get_service_health("1D") == [{"health_score": 100}]
    assert cm.request.await_args.kwargs["params"] == {"presetTime": "1D"}

    cm.request.return_value = None
    assert await mgr.get_service_health() == []
    assert await mgr.get_settings() == {}
    assert await mgr.get_usage() == {}
    assert await mgr.get_dashboard() == {}


async def test_device_manager_get_device_matches_any_mac_style(cm):
    mgr = DeviceManager(cm)
    cm.request.return_value = [{"mac": "AA:BB:CC:DD:EE:FF", "model": "UTP"}, "junk"]
    assert await mgr.list_devices() == [{"mac": "AA:BB:CC:DD:EE:FF", "model": "UTP"}]
    assert (await mgr.get_device("aabbccddeeff"))["model"] == "UTP"
    assert (await mgr.get_device("aa-bb-cc-dd-ee-ff"))["model"] == "UTP"
    with pytest.raises(UniFiNotFoundError):
        await mgr.get_device("001122334455")
    with pytest.raises(ValueError, match="12-digit"):
        await mgr.get_device("not-a-mac")


async def test_user_manager_get_user(cm):
    mgr = UserManager(cm)
    cm.request.return_value = [{"unique_id": "u1"}, {"unique_id": "u2"}]
    assert (await mgr.get_user("u2"))["unique_id"] == "u2"
    with pytest.raises(UniFiNotFoundError):
        await mgr.get_user("u3")


async def test_number_manager_tolerates_non_list(cm):
    mgr = NumberManager(cm)
    cm.request.return_value = {"unexpected": True}
    assert await mgr.list_numbers() == []
    assert await mgr.list_blocked_numbers() == []


async def test_call_manager_list_calls_paginates(cm):
    mgr = CallManager(cm)
    cm.request.return_value = {"calls": [{"uuid": "c1"}], "total_count": 47}
    assert await mgr.list_calls("u1", limit=5, offset=10) == {"calls": [{"uuid": "c1"}], "total_count": 47}
    assert cm.request.await_args.args == ("GET", "call_log/user/u1")
    assert cm.request.await_args.kwargs["params"] == {"limit": 5, "offset": 10}

    cm.request.return_value = None
    assert await mgr.list_calls("u1") == {"calls": [], "total_count": 0}


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"user_id": ""}, "user_id is required"),
        ({"user_id": "u1", "limit": 0}, "limit must be"),
        ({"user_id": "u1", "limit": MAX_CALL_PAGE + 1}, "limit must be"),
        ({"user_id": "u1", "offset": -1}, "offset must be"),
    ],
)
async def test_call_manager_list_calls_validates_before_request(cm, kwargs, message):
    with pytest.raises(ValueError, match=message):
        await CallManager(cm).list_calls(**kwargs)
    cm.request.assert_not_awaited()


async def test_call_manager_voicemail_and_transcript(cm):
    mgr = CallManager(cm)
    cm.request.return_value = {"uuid": "c1", "duration": "12"}
    assert (await mgr.get_voicemail("c1"))["uuid"] == "c1"
    assert cm.request.await_args.args == ("GET", "voicemail/data/c1")

    cm.request.return_value = None
    with pytest.raises(UniFiNotFoundError):
        await mgr.get_voicemail("c2")

    assert await mgr.get_transcript("c1") is None
    assert cm.request.await_args.kwargs["params"] == {"call_uuid": "c1", "transcript_source": "call"}

    cm.request.return_value = [{"event": "call_started"}]
    assert await mgr.get_call_flow("c1") == [{"event": "call_started"}]


async def test_callflow_manager_unwraps_switchboard(cm):
    mgr = CallFlowManager(cm)
    cm.request.return_value = {"entities": {"nodes": {"byId": {"swb_1": {"type": "sa"}}, "allIds": ["swb_1"]}}}
    assert await mgr.get_switchboard() == {"swb_1": {"type": "sa"}}
    cm.request.return_value = None
    assert await mgr.get_switchboard() == {}
    assert await mgr.list_groups() == []

    cm.request.return_value = [{"id": 1}]
    for method, path in [
        (mgr.list_groups, "group_list"),
        (mgr.list_ring_flows, "ring_flow"),
        (mgr.list_queues, "call_center/queue"),
        (mgr.list_parking_lots, "parking_lots"),
        (mgr.list_contacts, "contacts"),
        (mgr.list_recording_rules, "call_recording_rule"),
    ]:
        assert await method() == [{"id": 1}]
        assert cm.request.await_args.args == ("GET", path)
