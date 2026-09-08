"""One MCP client: HTTP, stdio, or inprocess. No catalog load on this path."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from typing import cast

from open_ux import __version__

DEFAULT_URL = "https://open-ux.dev/mcp"
PROTOCOL_VERSION = "2025-03-26"
CLIENT_NAME = "open-ux"
HOSTED_HINT = (
    "Hosted MCP needs OPEN_UX_API_KEY (uxmcp_). "
    "Request an invite at https://open-ux.dev/invite. Do not invent a key."
)
TRANSPORTS = ("http", "stdio", "inprocess")

JsonObject = dict[str, object]


class McpError(RuntimeError):
    """Transport or protocol failure."""


def endpoint() -> str:
    return (os.environ.get("OPEN_UX_URL") or DEFAULT_URL).strip() or DEFAULT_URL


def resolve_transport(explicit: str | None = None) -> str:
    if explicit:
        mode = explicit.strip().lower()
    else:
        mode = (os.environ.get("OPEN_UX_TRANSPORT") or "").strip().lower()
        if not mode:
            if (os.environ.get("OPEN_UX_API_KEY") or "").strip():
                return "http"
            return "inprocess"
    if mode not in TRANSPORTS:
        raise McpError(f"Unknown transport {mode!r}. Use http, stdio, or inprocess.")
    return mode


def transport() -> str:
    return resolve_transport()


def _auth_headers(url: str) -> dict[str, str]:
    key = (os.environ.get("OPEN_UX_API_KEY") or "").strip()
    if "open-ux.dev" in url and not key:
        raise McpError(HOSTED_HINT)
    headers: dict[str, str] = {}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    return headers


def _unwrap_tool_result(result: object) -> object:
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


def _parse_rpc_body(content_type: str, raw: bytes) -> JsonObject:
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
                return cast(JsonObject, msg)
        raise McpError("No JSON-RPC result in SSE stream.")
    msg = json.loads(text)
    if not isinstance(msg, dict):
        raise McpError("MCP response was not a JSON object.")
    return cast(JsonObject, msg)


def _http_post(
    url: str,
    payload: JsonObject,
    headers: dict[str, str],
    session_id: str | None,
) -> tuple[JsonObject, str | None]:
    req_headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
        "MCP-Protocol-Version": PROTOCOL_VERSION,
        "User-Agent": f"{CLIENT_NAME}/{__version__}",
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


def _rpc_result(msg: JsonObject) -> object:
    if "error" in msg and msg["error"] is not None:
        err = msg["error"]
        if isinstance(err, dict):
            raise McpError(str(err.get("message") or err))
        raise McpError(str(err))
    return msg.get("result")


class HttpSession:
    """One initialize + tools/list or tools/call against streamable HTTP."""

    def __init__(self, url: str, headers: dict[str, str]) -> None:
        self.url = url
        self.headers = headers
        self.session_id: str | None = None
        self._next_id = 0

    def _id(self) -> int:
        self._next_id += 1
        return self._next_id

    def request(self, method: str, params: JsonObject | None = None) -> object:
        payload: JsonObject = {
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

    def notify(self, method: str, params: JsonObject | None = None) -> None:
        payload: JsonObject = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        try:
            _http_post(self.url, payload, self.headers, self.session_id)
        except McpError:
            return


def _http_session() -> HttpSession:
    url = endpoint()
    session = HttpSession(url, _auth_headers(url))
    session.request(
        "initialize",
        {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": CLIENT_NAME, "version": __version__},
        },
    )
    session.notify("notifications/initialized")
    return session


def _summarize_tools(raw: object) -> list[dict[str, str]]:
    tools = raw.get("tools") if isinstance(raw, dict) else raw
    if not isinstance(tools, list):
        return []
    rows: list[dict[str, str]] = []
    for item in tools:
        name = getattr(item, "name", None) or (
            item.get("name") if isinstance(item, dict) else None
        )
        if not name:
            continue
        desc = getattr(item, "description", None)
        if desc is None and isinstance(item, dict):
            desc = item.get("description")
        rows.append({"name": str(name), "description": str(desc or "")[:160]})
    return rows


def _call_http(name: str, arguments: JsonObject) -> object:
    result = _http_session().request(
        "tools/call", {"name": name, "arguments": arguments}
    )
    return _unwrap_tool_result(result)


def _list_http() -> list[dict[str, str]]:
    return _summarize_tools(_http_session().request("tools/list", {}))


def _call_inprocess(name: str, arguments: JsonObject) -> object:
    from fastmcp import Client
    from open_ux.server import create_mcp

    async def _run() -> object:
        async with Client(create_mcp(hosted=False)) as client:
            result = await client.call_tool(name, arguments)
            return result.data

    return asyncio.run(_run())


def _list_inprocess() -> list[dict[str, str]]:
    from fastmcp import Client
    from open_ux.server import create_mcp

    async def _run() -> list[dict[str, str]]:
        async with Client(create_mcp(hosted=False)) as client:
            return _summarize_tools(await client.list_tools())

    return asyncio.run(_run())


def _stdio_command() -> list[str]:
    raw = (os.environ.get("OPEN_UX_STDIO_CMD") or "").strip()
    if raw:
        return raw.split()
    return [sys.executable, "-m", "open_ux", "stdio"]


def _write_stdio_message(proc: subprocess.Popen[bytes], payload: JsonObject) -> None:
    data = json.dumps(payload).encode("utf-8")
    header = f"Content-Length: {len(data)}\r\n\r\n".encode("ascii")
    assert proc.stdin is not None
    proc.stdin.write(header + data)
    proc.stdin.flush()


def _read_stdio_message(proc: subprocess.Popen[bytes]) -> JsonObject:
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
    return cast(JsonObject, msg)


def _stdio_session_call(method: str, params: JsonObject | None) -> object:
    try:
        return _stdio_fastmcp(method, params)
    except ImportError:
        return _stdio_framed(method, params)


def _stdio_fastmcp(method: str, params: JsonObject | None) -> object:
    from fastmcp import Client
    from fastmcp.client.transports import StdioTransport

    cmd = _stdio_command()
    stdio = StdioTransport(command=cmd[0], args=cmd[1:], keep_alive=False)

    async def _run() -> object:
        async with Client(stdio) as client:
            if method == "tools/list":
                return _summarize_tools(await client.list_tools())
            name = (params or {}).get("name")
            arguments = (params or {}).get("arguments") or {}
            if not isinstance(arguments, dict):
                raise McpError("stdio tools/call arguments must be an object.")
            result = await client.call_tool(str(name), arguments)
            return result.data

    return asyncio.run(_run())


def _stdio_framed(method: str, params: JsonObject | None) -> object:
    proc = subprocess.Popen(
        _stdio_command(),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    next_id = 0

    def request(rpc_method: str, rpc_params: JsonObject | None = None) -> object:
        nonlocal next_id
        next_id += 1
        payload: JsonObject = {
            "jsonrpc": "2.0",
            "id": next_id,
            "method": rpc_method,
        }
        if rpc_params is not None:
            payload["params"] = rpc_params
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
                "clientInfo": {"name": CLIENT_NAME, "version": __version__},
            },
        )
        _write_stdio_message(
            proc, {"jsonrpc": "2.0", "method": "notifications/initialized"}
        )
        result = request(method, params)
        if method == "tools/list":
            return _summarize_tools(result)
        return _unwrap_tool_result(result)
    finally:
        if proc.stdin:
            proc.stdin.close()
        proc.kill()
        proc.wait(timeout=5)


def call_tool(
    name: str,
    arguments: JsonObject | None = None,
    *,
    transport: str | None = None,
) -> object:
    args = arguments or {}
    mode = resolve_transport(transport)
    if mode == "inprocess":
        return _call_inprocess(name, args)
    if mode == "stdio":
        return _stdio_session_call(
            "tools/call", {"name": name, "arguments": args}
        )
    return _call_http(name, args)


def list_tools(*, transport: str | None = None) -> list[dict[str, str]]:
    mode = resolve_transport(transport)
    if mode == "inprocess":
        return _list_inprocess()
    if mode == "stdio":
        listed = _stdio_session_call("tools/list", {})
        if isinstance(listed, list):
            return listed
        return _summarize_tools(listed)
    return _list_http()
