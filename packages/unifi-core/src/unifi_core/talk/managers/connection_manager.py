"""Connection management for UniFi Talk.

Talk has no public API or API-key surface. All requests go through a UniFi OS
Console session: log in via ``/api/auth/login`` (cookie + CSRF token), then
proxy through ``/proxy/talk/api/...``.

Unlike Access, Talk returns bare JSON bodies (objects, arrays, or ``null``)
with no ``{"code": ..., "data": ...}`` envelope, and signals errors by HTTP
status alone.
"""

from __future__ import annotations

import asyncio
import functools
import logging
import ssl
from typing import Any

import aiohttp

from unifi_core.auth import AuthenticationStatus
from unifi_core.exceptions import UniFiAuthError, UniFiConnectionError, UniFiNotFoundError, UniFiPermissionError

logger = logging.getLogger(__name__)

_REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=30)


class TalkConnectionManager:
    """Manages the UniFi OS session used to reach the Talk application.

    Parameters
    ----------
    host:
        IP or hostname of the UniFi OS Console running Talk.
    username:
        Local admin username.
    password:
        Local admin password.
    port:
        HTTPS port for the UniFi OS Console (default 443).
    verify_ssl:
        Whether to verify the server's TLS certificate.
    """

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        port: int = 443,
        verify_ssl: bool = False,
    ) -> None:
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.verify_ssl = verify_ssl

        self._session: aiohttp.ClientSession | None = None
        self._csrf_token: str = ""
        self._auth_lock = asyncio.Lock()
        self._available = False
        self._initialized = False

    @functools.cached_property
    def _ssl_context(self) -> ssl.SSLContext | bool:
        """Return an SSL context appropriate for the current verify_ssl setting."""
        if self.verify_ssl:
            return True
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def initialize(self) -> bool:
        """Log in to the UniFi OS Console. Returns ``True`` on success."""
        if self._initialized and self._available:
            return True
        if not (self.host and self.username and self.password):
            logger.error("[talk-cm] Host, username and password are required; Talk has no API-key path.")
            self._initialized = True
            return False

        try:
            self._session = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=self._ssl_context),
                cookie_jar=aiohttp.CookieJar(unsafe=True),
                timeout=_REQUEST_TIMEOUT,
            )
            await self._login()
            self._available = True
            logger.info("[talk-cm] Session established via %s:%s", self.host, self.port)
        except Exception as exc:
            logger.error("[talk-cm] Login failed: %s", type(exc).__name__)
            await self._close_session()
            self._available = False
        self._initialized = True
        return self._available

    async def _login(self) -> None:
        """Authenticate to the UniFi OS Console and store the CSRF token."""
        url = f"https://{self.host}:{self.port}/api/auth/login"
        payload = {"username": self.username, "password": self.password}

        async with self._session.post(url, json=payload) as resp:
            if resp.status != 200:
                # The response body can echo account details; report status only.
                raise UniFiAuthError(f"Talk login failed: HTTP {resp.status}")
            self._csrf_token = resp.headers.get("x-updated-csrf-token", resp.headers.get("x-csrf-token", ""))

    # ------------------------------------------------------------------
    # Requests
    # ------------------------------------------------------------------

    async def request(self, method: str, path: str, *, operation: str, **kwargs: Any) -> Any:
        """Make a request to ``/proxy/talk/api/<path>`` and return the parsed JSON body.

        Parameters
        ----------
        method:
            HTTP method.
        path:
            API path relative to ``/proxy/talk/api/``.
        operation:
            Short description used in error messages (e.g. ``"List Talk devices"``).
        **kwargs:
            Forwarded to ``aiohttp.ClientSession.request`` (e.g. ``params=``, ``json=``).

        Raises
        ------
        UniFiConnectionError
            If the session is unavailable or the request fails.
        UniFiNotFoundError
            On HTTP 404.
        UniFiPermissionError
            On HTTP 403.
        """
        if not self._available or self._session is None:
            raise UniFiConnectionError(f"{operation} failed: Talk session is not available.")

        url = f"https://{self.host}:{self.port}/proxy/talk/api/{path.lstrip('/')}"
        try:
            token_before = self._csrf_token
            async with self._session.request(method, url, headers={"X-CSRF-Token": self._csrf_token}, **kwargs) as resp:
                if resp.status != 401:
                    return await self._parse(resp, operation, path)

            async with self._auth_lock:
                # Skip re-auth if another coroutine already refreshed the session.
                if self._csrf_token == token_before:
                    logger.info("[talk-cm] Session expired, re-authenticating...")
                    await self._login()
            async with self._session.request(method, url, headers={"X-CSRF-Token": self._csrf_token}, **kwargs) as resp:
                return await self._parse(resp, operation, path)
        except (UniFiAuthError, UniFiConnectionError, UniFiNotFoundError, UniFiPermissionError):
            raise
        except (TimeoutError, aiohttp.ClientError, OSError) as exc:
            raise UniFiConnectionError(f"{operation} failed: {type(exc).__name__}") from exc

    @staticmethod
    async def _parse(resp: aiohttp.ClientResponse, operation: str, path: str) -> Any:
        # Talk error bodies can echo phone numbers and names; report status only.
        if resp.status == 404:
            raise UniFiNotFoundError("talk_resource", path, f"{operation} failed: not found (HTTP 404)")
        if resp.status == 403:
            raise UniFiPermissionError(
                f"{operation} failed: HTTP 403. The account needs Talk view or manage permission."
            )
        if resp.status == 401:
            raise UniFiAuthError(f"{operation} failed: HTTP 401 after re-authentication")
        if resp.status != 200:
            raise UniFiConnectionError(f"{operation} failed: HTTP {resp.status}")
        try:
            return await resp.json(content_type=None)
        except ValueError as exc:
            raise UniFiConnectionError(f"{operation} failed: response was not JSON") from exc

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_connected(self) -> bool:
        """Return ``True`` if the session is initialised and usable."""
        return self._initialized and self._available and self._session is not None

    @property
    def authentication_status(self) -> AuthenticationStatus:
        return AuthenticationStatus(
            session_configured=bool(self.username and self.password),
            api_key_configured=False,
            session_available=self.is_connected,
            api_key_available=False,
        )

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    async def _close_session(self) -> None:
        if self._session is not None and not self._session.closed:
            try:
                await self._session.close()
            except Exception:
                logger.debug("[talk-cm] Error closing session", exc_info=True)
        self._session = None

    async def close(self) -> None:
        """Gracefully shut down the session."""
        await self._close_session()
        self._available = False
        self._initialized = False
        logger.info("[talk-cm] Connection closed.")
