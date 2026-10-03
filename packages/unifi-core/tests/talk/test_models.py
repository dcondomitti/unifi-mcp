"""Tests for the Talk field models: projection and secret exclusion."""

from __future__ import annotations

from unifi_core.talk.models import calls, devices, groups, numbers, system, users


def test_device_model_drops_controller_secrets():
    raw = {
        "mac": "aabbccddeeff",
        "display_name": "Front Desk",
        "sip_reg": True,
        "user": "Jane Doe",
        "user_id": "u1",
        "update_available": "",
        "hashed_key": "deadbeef",
        "anonymous_device_id": "anon",
        "additional_config": {"sip_password": "hunter2", "ext": "100"},
    }
    dumped = devices.from_controller(raw).model_dump(exclude_none=True)
    assert dumped == {
        "mac": "aabbccddeeff",
        "display_name": "Front Desk",
        "sip_registered": True,
        "user_id": "u1",
        "user_name": "Jane Doe",
    }
    assert "hunter2" not in str(dumped)


def test_user_model_drops_scopes_keys_and_sip_password():
    raw = {
        "unique_id": "u1",
        "full_name": "Jane Doe",
        "user_email": "jane@example.com",
        "email": "",
        "user_status": "ACTIVE",
        "ext": "100",
        "sip_password": "hunter2",
        "scopes": ["a"] * 100,
        "api_keys": [{"key": "k"}],
        "nfc_token": "tok",
        "did_list": None,
        "ring_groups": [{"id": 1, "uuid": "g1", "name": "Sales", "member_list": ["u1"]}],
        "devices": [{"mac": "aabbccddeeff", "model": "UTP", "hashed_key": "deadbeef"}],
    }
    dumped = users.from_controller(raw).model_dump(exclude_none=True)
    assert dumped == {
        "unique_id": "u1",
        "full_name": "Jane Doe",
        "email": "jane@example.com",
        "status": "ACTIVE",
        "ext": "100",
        "ring_groups": [{"id": 1, "uuid": "g1", "name": "Sales"}],
        "devices": [{"mac": "aabbccddeeff", "model": "UTP"}],
    }


def test_number_model_flattens_routing_targets():
    raw = {
        "did": "+15551234567",
        "plan": "standard",
        "sms_capable": True,
        "sid": "PNxxxx",
        "group_data": {"id": 4, "did": "+15551234567", "name": "Sales"},
        "smart_attendant": {"id": "swb_4", "title": "Main Menu", "greeting": "hello"},
    }
    assert numbers.from_controller(raw).model_dump(exclude_none=True) == {
        "did": "+15551234567",
        "plan": "standard",
        "sms_capable": True,
        "group_id": 4,
        "group_name": "Sales",
        "smart_attendant_id": "swb_4",
        "smart_attendant_title": "Main Menu",
    }


def test_call_models():
    call = calls.call_from_controller(
        {"uuid": "c1", "from": "100", "to": "+15551234567", "direction": "out", "status": "accepted", "duration": 42}
    ).model_dump(exclude_none=True)
    assert call == {
        "uuid": "c1",
        "direction": "out",
        "status": "accepted",
        "duration": 42,
        "from_number": "100",
        "to_number": "+15551234567",
    }

    event = calls.call_event_from_controller({"event": "vm_msg_recorded", "event_data": None}).model_dump()
    assert event["event"] == "vm_msg_recorded"
    assert event["event_data"] == {}

    voicemail = calls.voicemail_from_controller({"uuid": "c1", "duration": 12, "vm_left_for_ext": "100"})
    assert voicemail.duration == "12"


def test_group_model_normalizes_null_lists():
    group = groups.from_controller({"id": 4, "name": "Sales", "member_list": None, "did_list": ["+15551234567"]})
    assert group.member_list == []
    assert group.did_list == ["+15551234567"]


def test_system_models():
    info = system.system_info_from_controller(
        {"version": "5.4.4", "host_device_serial": "SERIAL", "owner_sso_id": "sso", "controller_latitude": 1.0}
    ).model_dump(exclude_none=True)
    assert info == {"version": "5.4.4"}

    dashboard = system.dashboard_from_controller(
        {"consoleName": "HQ", "talkVersion": "5.4.4", "deviceCount": 2, "onlineDevicesCount": 2, "gatewayIp": "1.2.3.4"}
    ).model_dump(exclude_none=True)
    assert dashboard == {"console_name": "HQ", "talk_version": "5.4.4", "device_count": 2, "online_devices_count": 2}


def test_all_talk_fields_are_read_only():
    for module in (calls, devices, groups, numbers, system, users):
        assert module.MUTABLE_FIELDS == frozenset()
        assert module.READ_ONLY_FIELDS


def test_unexpected_field_type_drops_the_field_not_the_row():
    user = users.from_controller({"unique_id": "u1", "ext": ["not", "a", "string"], "outbound_caller_id": 7})
    dumped = user.model_dump(exclude_none=True)
    assert dumped["unique_id"] == "u1"
    assert dumped["outbound_caller_id"] == 7
    assert "ext" not in dumped

    call = calls.call_from_controller({"uuid": "c1", "duration": "not-a-number", "direction": "in"})
    assert call.model_dump(exclude_none=True) == {"uuid": "c1", "direction": "in"}
