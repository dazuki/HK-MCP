"""Bearer-token-autentisering för HTTP-transport.

ASGI-middleware som kräver en giltig token i `Authorization: Bearer <token>`.
Tillåter flera tokens samtidigt för rotation utan downtime.
"""

from __future__ import annotations

import hmac
from collections.abc import Awaitable, Callable
from typing import Any

ASGIReceive = Callable[[], Awaitable[dict[str, Any]]]
ASGISend = Callable[[dict[str, Any]], Awaitable[None]]
ASGIApp = Callable[[dict[str, Any], ASGIReceive, ASGISend], Awaitable[None]]


async def _send_401(send: ASGISend, realm: str) -> None:
    body = b'{"error":"unauthorized"}'
    await send({
        "type": "http.response.start",
        "status": 401,
        "headers": [
            (b"content-type", b"application/json"),
            (b"www-authenticate", f'Bearer realm="{realm}"'.encode()),
            (b"content-length", str(len(body)).encode()),
        ],
    })
    await send({"type": "http.response.body", "body": body})


def bearer_token_middleware(
    app: ASGIApp,
    tokens: list[str],
    realm: str = "mcp",
    exempt_paths: list[str] | None = None,
) -> ASGIApp:
    """Wrappa en ASGI-app med Bearer-token-kontroll.

    Args:
        app: Inre ASGI-applikation.
        tokens: Lista med giltiga tokens. Fler än en tillåts för rotation.
        realm: Värde för WWW-Authenticate-headern vid 401.
        exempt_paths: Stigar som släpps igenom utan auth. Strängar som slutar
            med '/' tolkas som prefix, övriga som exakt matchning.

    Returns:
        Ny ASGI-app som släpper igenom om headern `Authorization: Bearer <token>`
        matchar någon token med konstanttidsjämförelse, annars svarar 401.
    """
    encoded = [t.encode() for t in tokens]
    exact = {p for p in (exempt_paths or []) if not p.endswith("/") or p == "/"}
    prefixes = tuple(p for p in (exempt_paths or []) if p.endswith("/") and p != "/")

    def _is_exempt(path: str) -> bool:
        return path in exact or path.startswith(prefixes)

    async def middleware(
        scope: dict[str, Any],
        receive: ASGIReceive,
        send: ASGISend,
    ) -> None:
        if scope["type"] != "http":
            await app(scope, receive, send)
            return

        if _is_exempt(scope.get("path", "")):
            await app(scope, receive, send)
            return

        auth_header = b""
        for name, value in scope.get("headers", []):
            if name == b"authorization":
                auth_header = value
                break

        if not auth_header.startswith(b"Bearer "):
            await _send_401(send, realm)
            return

        provided = auth_header[7:]
        if not any(hmac.compare_digest(provided, t) for t in encoded):
            await _send_401(send, realm)
            return

        await app(scope, receive, send)

    return middleware
