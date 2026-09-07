"""Thin MCP client for Open UX skill scripts.

Hosted (default): streamable HTTP at https://open-ux.dev/mcp + OPEN_UX_API_KEY
(uxmcp_). Self-host: OPEN_UX_URL, or OPEN_UX_TRANSPORT=stdio
(`python -m open_ux stdio`). Tests: OPEN_UX_TRANSPORT=inprocess (create_mcp).
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from typing import Any

DEFAULT_URL = "https://open-ux.dev/mcp"
PROTOCOL_VERSION = "2025-03-26"
CLIENT_NAME = "open-ux-scripts"
CLIENT_VERSION = "0.1.0"
HOSTED_HINT = (
    "Hosted MCP needs OPEN_UX_API_KEY (uxmcp_). "
    "Request an invite at https://open-ux.dev/invite. Do not invent a key."
)


class McpError(RuntimeError):
    """Transport or protocol failure. Tool payloads with an error key are not this."""


def endpoint() -> str:
    return (os.environ.get("OPEN_UX_URL") or DEFAULT_URL).strip() or DEFAULT_URL


def transport() -> str:
    return (os.environ.get("OPEN_UX_TRANSPORT") or "http").strip().lower() or "http"


def call_tool(name: str, arguments: dict[str, Any] | None = None) -> Any:
    """Call one MCP tool. Returns the unwrapped tool payload (a dict)."""
    args = arguments or {}
    mode = transport()
    if mode == "inprocess":
        return _call_inprocess(name, args)
    if mode == "stdio":
        return _call_stdio(name, args)
    return _call_http(name, args)


def dump(payload: Any) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def fail(message: str, *, code: int = 2) -> int:
    dump({"error": message})
    return code


def _auth_headers(url: str) -> dict[str, str]:
    key = (os.environ.get("OPEN_UX_API_KEY") or "").strip()
    hosted = "open-ux.dev" in url
    if hosted and not key:
        raise McpError(HOSTED_HINT)
    headers: dict[str, str] = {}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    return headers


def _unwrap_tool_result(result: Any) -> Any:
    if not isinstance(result, dict):
        return result
    if result.get("isError"):
        texts = [
            str(item.get("text") or "")
            for item in (result.get("content") or [])
            if isinstance(item, dict)
        ]
        raise McpError("; ".join(t for t in texts if t) or "MCP tool error.")
    structured = result.get("structuredContent")
    if structured is not None:
        return structured
    texts = [
        str(item.get("text") or "")
        for item in (result.get("content") or [])
        if isinstance(item, dict) and item.get("text")
    ]
    if len(texts) == 1:
        try:
            return json.loads(texts[0])
        except json.JSONDecodeError:
            return {"text": texts[0]}
    if texts:
        return {"text": "\n".join(texts)}
    return result


def _parse_rpc_body(content_type: str, raw: bytes) -> dict[str, Any]:
    text = raw.decode("utf-8")
    if "text/event-stream" in content_type:
        for block in text.split("\n\n"):
            data_lines = [
                line[5:].lstrip()
                for line in block.splitlines()
                if line.startswith("data:")
            ]
            if not data_lines:
                continue
            msg = json.loads("\n".join(data_lines))
            if isinstance(msg, dict) and ("result" in msg or "error" in msg):
                return msg
        raise McpError("No JSON-RPC result in SSE stream.")
    msg = json.loads(text)
    if not isinstance(msg, dict):
        raise McpError("MCP response was not a JSON object.")
    return msg


def _http_post(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    session_id: str | None,
) -> tuple[dict[str, Any], str | None]:
    req_headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
        "MCP-Protocol-Version": PROTOCOL_VERSION,
        "User-Agent": f"{CLIENT_NAME}/{CLIENT_VERSION}",
        **headers,
    }
    if session_id:
        req_headers["mcp-session-id"] = session_id
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=req_headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
            content_type = response.headers.get("Content-Type") or ""
            new_session = response.headers.get("mcp-session-id") or session_id
            status = getattr(response, "status", 200)
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        if exc.code == 401:
            raise McpError(HOSTED_HINT) from exc
        raise McpError(f"HTTP {exc.code}: {err_body[:400] or exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise McpError(f"Could not reach {url}: {exc.reason}") from exc
    if status >= 400:
        raise McpError(f"HTTP {status}")
    return _parse_rpc_body(content_type, raw), new_session


def _rpc_result(msg: dict[str, Any]) -> Any:
    if "error" in msg and msg["error"] is not None:
        err = msg["error"]
        if isinstance(err, dict):
            raise McpError(str(err.get("message") or err))
        raise McpError(str(err))
    return msg.get("result")


class HttpSession:
    """One initialize + tools/call against streamable HTTP."""

    def __init__(self, url: str, headers: dict[str, str]):
        self.url = url
        self.headers = headers
        self.session_id: str | None = None
        self._next_id = 0

    def _id(self) -> int:
        self._next_id += 1
        return self._next_id

    def request(self, method: str, params: dict[str, Any] | None = None) -> Any:
        payload: dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": self._id(),
            "method": method,
        }
        if params is not None:
            payload["params"] = params
        msg, self.session_id = _http_post(
            self.url, payload, self.headers, self.session_id
        )
        return _rpc_result(msg)

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        payload: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        try:
            _http_post(self.url, payload, self.headers, self.session_id)
        except McpError:
            return


def _call_http(name: str, arguments: dict[str, Any]) -> Any:
    url = endpoint()
    session = HttpSession(url, _auth_headers(url))
    session.request(
        "initialize",
        {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": CLIENT_NAME, "version": CLIENT_VERSION},
        },
    )
    session.notify("notifications/initialized")
    result = session.request("tools/call", {"name": name, "arguments": arguments})
    return _unwrap_tool_result(result)


def _call_inprocess(name: str, arguments: dict[str, Any]) -> Any:
    from fastmcp import Client
    from open_ux.server import create_mcp

    async def _run() -> Any:
        async with Client(create_mcp(hosted=False)) as client:
            result = await client.call_tool(name, arguments)
            return result.data

    return asyncio.run(_run())


def _stdio_command() -> list[str]:
    raw = (os.environ.get("OPEN_UX_STDIO_CMD") or "").strip()
    if raw:
        return raw.split()
    return [sys.executable, "-m", "open_ux", "stdio"]


def _write_stdio_message(proc: subprocess.Popen[bytes], payload: dict[str, Any]) -> None:
    data = json.dumps(payload).encode("utf-8")
    header = f"Content-Length: {len(data)}\r\n\r\n".encode("ascii")
    assert proc.stdin is not None
    proc.stdin.write(header + data)
    proc.stdin.flush()


def _read_stdio_message(proc: subprocess.Popen[bytes]) -> dict[str, Any]:
    assert proc.stdout is not None
    headers: dict[str, str] = {}
    while True:
        line = proc.stdout.readline()
        if not line:
            raise McpError("stdio MCP closed before a response.")
        if line in (b"\r\n", b"\n"):
            if headers:
                break
            continue
        decoded = line.decode("ascii", errors="replace").rstrip("\r\n")
        if ":" in decoded:
            key, value = decoded.split(":", 1)
            headers[key.strip().lower()] = value.strip()
    length = int(headers.get("content-length") or "0")
    raw = proc.stdout.read(length)
    msg = json.loads(raw.decode("utf-8"))
    if not isinstance(msg, dict):
        raise McpError("stdio MCP response was not a JSON object.")
    return msg


def _call_stdio(name: str, arguments: dict[str, Any]) -> Any:
    try:
        return _call_stdio_fastmcp(name, arguments)
    except ImportError:
        return _call_stdio_framed(name, arguments)


def _call_stdio_fastmcp(name: str, arguments: dict[str, Any]) -> Any:
    from fastmcp import Client
    from fastmcp.client.transports import StdioTransport

    cmd = _stdio_command()
    stdio = StdioTransport(command=cmd[0], args=cmd[1:], keep_alive=False)

    async def _run() -> Any:
        async with Client(stdio) as client:
            result = await client.call_tool(name, arguments)
            return result.data

    return asyncio.run(_run())


def _call_stdio_framed(name: str, arguments: dict[str, Any]) -> Any:
    proc = subprocess.Popen(
        _stdio_command(),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    next_id = 0

    def request(method: str, params: dict[str, Any] | None = None) -> Any:
        nonlocal next_id
        next_id += 1
        payload: dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": next_id,
            "method": method,
        }
        if params is not None:
            payload["params"] = params
        _write_stdio_message(proc, payload)
        while True:
            msg = _read_stdio_message(proc)
            if msg.get("id") == next_id or "error" in msg:
                return _rpc_result(msg)

    try:
        request(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": CLIENT_NAME, "version": CLIENT_VERSION},
            },
        )
        _write_stdio_message(
            proc, {"jsonrpc": "2.0", "method": "notifications/initialized"}
        )
        result = request("tools/call", {"name": name, "arguments": arguments})
        return _unwrap_tool_result(result)
    finally:
        if proc.stdin:
            proc.stdin.close()
        proc.kill()
        proc.wait(timeout=5)


def main_call(name: str, arguments: dict[str, Any] | None = None) -> int:
    try:
        dump(call_tool(name, arguments))
        return 0
    except McpError as exc:
        dump({"error": str(exc)})
        return 1
