"""Tests for TalkConnectionManager session handling."""

from __future__ import annotations

import json
from typing import Any

import pytest
from unifi_core.exceptions import UniFiAuthError, UniFiConnectionError, UniFiNotFoundError, UniFiPermissionError
from unifi_core.talk.managers import connection_manager as module
from unifi_core.talk.managers.connection_manager import TalkConnectionManager

LOGIN = "https://192.168.1.1:443/api/auth/login"
API = "https://192.168.1.1:443/proxy/talk/api"


class FakeResponse:
    def __init__(self, status: int = 200, body: str = "{}", headers: dict[str, str] | None = None) -> None:
        self.status = status
        self._body = body
        self.headers = headers or {}

    async def json(self, content_type: Any = None) -> Any:
        return json.loads(self._body)

    async def __aenter__(self) -> "FakeResponse":
        return self

    async def __aexit__(self, *exc: Any) -> None:
        return None


class FakeSession:
    """Scripted stand-in for aiohttp.ClientSession; responses are consumed in order."""

    def __init__(self, responses: list[FakeResponse]) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, str, dict[str, Any]]] = []
        self.closed = False

    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append((method, url, kwargs))
        return self.responses.pop(0)

    def post(self, url: str, **kwargs: Any) -> FakeResponse:
        return self.request("POST", url, **kwargs)

    async def close(self) -> None:
        self.closed = True


def login_ok(token: str = "csrf-1") -> FakeResponse:
    return FakeResponse(headers={"x-csrf-token": token})


@pytest.fixture
def connect(monkeypatch):
    """Return a factory that initializes a manager against scripted responses."""

    async def _connect(*responses: FakeResponse) -> tuple[TalkConnectionManager, FakeSession]:
        session = FakeSession([login_ok(), *responses])
        monkeypatch.setattr(module.aiohttp, "ClientSession", lambda **kwargs: session)
        cm = TalkConnectionManager(host="192.168.1.1", username="admin", password="secret")
        assert await cm.initialize() is True
        return cm, session

    return _connect


async def test_initialize_requires_credentials():
    cm = TalkConnectionManager(host="192.168.1.1", username="", password="")
    assert await cm.initialize() is False
    assert cm.is_connected is False
    assert cm.authentication_status.session_configured is False


async def test_initialize_login_failure_leaves_manager_disconnected(monkeypatch):
    session = FakeSession([FakeResponse(status=403, body="account locked for admin")])
    monkeypatch.setattr(module.aiohttp, "ClientSession", lambda **kwargs: session)
    cm = TalkConnectionManager(host="192.168.1.1", username="admin", password="secret")

    assert await cm.initialize() is False
    assert cm.is_connected is False
    assert session.closed is True
    with pytest.raises(UniFiConnectionError, match="session is not available"):
        await cm.request("GET", "info", operation="Get Talk system info")


async def test_login_posts_credentials_and_stores_csrf(connect):
    cm, session = await connect()
    method, url, kwargs = session.calls[0]
    assert (method, url) == ("POST", LOGIN)
    assert kwargs["json"] == {"username": "admin", "password": "secret"}
    assert cm._csrf_token == "csrf-1"
    assert cm.is_connected is True
    assert cm.authentication_status.session_available is True
    assert cm.authentication_status.api_key_configured is False


async def test_request_returns_bare_json_and_sends_csrf(connect):
    cm, session = await connect(FakeResponse(body='[{"mac": "aabbccddeeff"}]'))
    result = await cm.request("GET", "/devices", operation="List Talk devices", params={"a": 1})
    assert result == [{"mac": "aabbccddeeff"}]
    method, url, kwargs = session.calls[1]
    assert (method, url) == ("GET", f"{API}/devices")
    assert kwargs["headers"] == {"X-CSRF-Token": "csrf-1"}
    assert kwargs["params"] == {"a": 1}


async def test_request_accepts_null_body(connect):
    cm, _ = await connect(FakeResponse(body="null"))
    assert await cm.request("GET", "transcript/by_call_uuid", operation="Get Talk call transcript") is None


async def test_request_reauthenticates_once_on_401(connect):
    cm, session = await connect(FakeResponse(status=401), login_ok("csrf-2"), FakeResponse(body='{"version": "5.4.4"}'))
    assert await cm.request("GET", "info", operation="Get Talk system info") == {"version": "5.4.4"}
    assert [call[1] for call in session.calls] == [LOGIN, f"{API}/info", LOGIN, f"{API}/info"]
    assert session.calls[3][2]["headers"] == {"X-CSRF-Token": "csrf-2"}


async def test_request_raises_auth_error_when_still_401_after_reauth(connect):
    cm, _ = await connect(FakeResponse(status=401), login_ok("csrf-2"), FakeResponse(status=401))
    with pytest.raises(UniFiAuthError):
        await cm.request("GET", "info", operation="Get Talk system info")


@pytest.mark.parametrize(
    ("status", "exc"),
    [(404, UniFiNotFoundError), (403, UniFiPermissionError), (500, UniFiConnectionError), (400, UniFiConnectionError)],
)
async def test_request_maps_http_errors_without_echoing_body(connect, status, exc):
    cm, _ = await connect(FakeResponse(status=status, body="caller +15551234567 Jane Doe"))
    with pytest.raises(exc) as info:
        await cm.request("GET", "voicemail/data/c1", operation="Get Talk voicemail")
    assert "Get Talk voicemail failed" in str(info.value)
    assert "+15551234567" not in str(info.value)
    assert "Jane" not in str(info.value)


async def test_request_rejects_non_json_body(connect):
    cm, _ = await connect(FakeResponse(body="<html>"))
    with pytest.raises(UniFiConnectionError, match="not JSON"):
        await cm.request("GET", "info", operation="Get Talk system info")


async def test_request_wraps_transport_errors(connect):
    cm, session = await connect()

    def boom(method: str, url: str, **kwargs: Any) -> FakeResponse:
        raise module.aiohttp.ClientConnectionError("10.0.0.1 refused")

    session.request = boom
    with pytest.raises(UniFiConnectionError) as info:
        await cm.request("GET", "info", operation="Get Talk system info")
    assert str(info.value) == "Get Talk system info failed: ClientConnectionError"


async def test_close_resets_state(connect):
    cm, session = await connect()
    await cm.close()
    assert session.closed is True
    assert cm.is_connected is False
