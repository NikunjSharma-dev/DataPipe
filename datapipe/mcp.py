"""
datapipe/mcp.py — Model Context Protocol (MCP) Server.

Exposes DataPipe search, token context formatting, and session memory to
AI assistants (Claude Desktop, Cursor, AGY, VS Code) via standard MCP stdio JSON-RPC.

Usage:
    datapipe mcp my_pipeline.py
"""

from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datapipe.engine import Pipeline


class MCPServer:
    """Stdio JSON-RPC 2.0 Model Context Protocol server for DataPipe."""

    def __init__(self, pipeline: "Pipeline") -> None:
        self.pipeline = pipeline

    def run_stdio(self) -> None:
        """Read line-delimited or content-length JSON-RPC requests from stdin."""
        sys.stderr.write(f"[datapipe-mcp] Serving pipeline '{self.pipeline.name}' over stdio...\n")
        sys.stderr.flush()

        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue
                
                request = json.loads(line)
                response = self.handle_request(request)
                if response is not None:
                    sys.stdout.write(json.dumps(response) + "\n")
                    sys.stdout.flush()
            except KeyboardInterrupt:
                break
            except Exception as exc:
                sys.stderr.write(f"[datapipe-mcp] Error: {exc}\n")
                sys.stderr.flush()

    def handle_request(self, req: dict[str, Any]) -> dict[str, Any] | None:
        msg_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "datapipe-mcp",
                        "version": "2.0.0",
                    },
                },
            }

        if method == "notifications/initialized":
            return None

        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": [
                        {
                            "name": "datapipe_search",
                            "description": "Perform BM25 full-text search across indexed code, docs, and structured data.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "query": {"type": "string", "description": "Search query keywords"},
                                    "limit": {"type": "integer", "default": 20, "description": "Max results"},
                                },
                                "required": ["query"],
                            },
                        },
                        {
                            "name": "datapipe_get_context",
                            "description": "Build token-budgeted context block for LLM prompt injection with compression metrics.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "query": {"type": "string", "description": "Topic or query to build context for"},
                                    "max_tokens": {"type": "integer", "default": 4000, "description": "Max token budget"},
                                    "session_key": {"type": "string", "description": "Optional session memory key"},
                                },
                                "required": ["query"],
                            },
                        },
                        {
                            "name": "datapipe_session_snapshot",
                            "description": "Retrieve active agent session state, recent tool calls, and file edit history.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "session_key": {"type": "string", "description": "Session identifier key"},
                                },
                                "required": ["session_key"],
                            },
                        },
                        {
                            "name": "datapipe_sql",
                            "description": "Run raw SQL query against SQLite index database.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "sql": {"type": "string", "description": "SQL query to execute"},
                                },
                                "required": ["sql"],
                            },
                        },
                        {
                            "name": "datapipe_stats",
                            "description": "Get index statistics, total rows, and file count for pipeline.",
                            "inputSchema": {"type": "object", "properties": {}},
                        },
                    ]
                },
            }

        if method == "tools/call":
            tool_name = params.get("name")
            args = params.get("arguments", {})
            try:
                res_text = self._call_tool(tool_name, args)
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": res_text}],
                    },
                }
            except Exception as exc:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32603, "message": str(exc)},
                }

        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }

    def _call_tool(self, tool_name: str, args: dict[str, Any]) -> str:
        if tool_name == "datapipe_search":
            query = args.get("query", "")
            limit = args.get("limit", 20)
            df = self.pipeline.search(query, limit=limit)
            if df.empty:
                return "No search results found."
            return df.to_json(orient="records", indent=2)

        if tool_name == "datapipe_get_context":
            from datapipe.context import ContextBuilder
            query = args.get("query", "")
            max_tokens = args.get("max_tokens", 4000)
            session_key = args.get("session_key")
            ctx = ContextBuilder(self.pipeline).build_context(
                query, max_tokens=max_tokens, session_key=session_key
            )
            return json.dumps(ctx, indent=2)

        if tool_name == "datapipe_session_snapshot":
            from datapipe.memory import SessionMemory
            key = args.get("session_key", "")
            mem = SessionMemory(self.pipeline.store)
            snapshot = mem.get_resume_snapshot(key)
            return snapshot or f"No session found for key: {key}"

        if tool_name == "datapipe_sql":
            sql = args.get("sql", "")
            df = self.pipeline.sql(sql)
            if df.empty:
                return "(empty result set)"
            return df.to_json(orient="records", indent=2)

        if tool_name == "datapipe_stats":
            stats = self.pipeline.stats()
            return json.dumps(stats, indent=2)

        raise ValueError(f"Unknown tool: {tool_name}")
