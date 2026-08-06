"""
datapipe/webui.py — Web UI Dashboard & Interactive Pipeline Visualizer.

Provides an HTTP server serving a modern, high-tech dashboard for hackathon demos.
Features:
- Live Pipeline Data Flow Visualizer
- AI Context Window Compression Simulator
- Full-Text Search Playground with BM25 rankings
- Agent Session Memory Timeline
- SQLite Database & File Explorer

Usage:
    datapipe ui my_pipeline.py [--port 8500]
"""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datapipe.engine import Pipeline


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DataPipe v2 — AI Context & Multimodal Data Pipeline</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #0b0f19;
            --bg-card: #131b2e;
            --bg-card-hover: #1a243d;
            --border-color: #233152;
            --accent-blue: #3b82f6;
            --accent-cyan: #06b6d4;
            --accent-purple: #8b5cf6;
            --accent-emerald: #10b981;
            --accent-amber: #f59e0b;
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
            --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: var(--bg-dark);
            color: var(--text-main);
            font-family: var(--font-sans);
            line-height: 1.5;
            min-height: 100vh;
            padding: 24px;
        }

        /* Header */
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 24px;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 24px;
        }
        .logo-group {
            display: flex;
            align-items: center;
            gap: 16px;
        }
        .logo-icon {
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 20px;
            box-shadow: 0 0 20px rgba(59, 130, 246, 0.4);
        }
        h1 { font-size: 22px; font-weight: 700; background: linear-gradient(90deg, #fff, #93c5fd); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .subtitle { font-size: 13px; color: var(--text-muted); }
        .badge {
            background: rgba(16, 185, 129, 0.15);
            color: var(--accent-emerald);
            border: 1px solid rgba(10, 185, 129, 0.3);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .pulse {
            width: 8px;
            height: 8px;
            background-color: var(--accent-emerald);
            border-radius: 50%;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }

        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }
        .stat-card {
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 14px;
            padding: 20px;
            transition: transform 0.2s, border-color 0.2s;
        }
        .stat-card:hover {
            transform: translateY(-2px);
            border-color: var(--accent-blue);
        }
        .stat-label { font-size: 12px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
        .stat-value { font-size: 28px; font-weight: 700; color: #fff; font-family: var(--font-mono); }
        .stat-subtext { font-size: 12px; color: var(--accent-cyan); margin-top: 4px; }

        /* Tabs Navigation */
        .nav-tabs {
            display: flex;
            gap: 8px;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 24px;
        }
        .tab-btn {
            background: none;
            border: none;
            color: var(--text-muted);
            padding: 12px 20px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.2s;
        }
        .tab-btn:hover { color: var(--text-main); }
        .tab-btn.active {
            color: var(--accent-blue);
            border-bottom-color: var(--accent-blue);
        }

        /* Tab Content Panels */
        .tab-panel { display: none; }
        .tab-panel.active { display: block; }

        /* Flow Visualizer */
        .visualizer-card {
            background-color: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 28px;
            margin-bottom: 24px;
        }
        .flow-container {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            position: relative;
            padding: 30px 10px;
            overflow-x: auto;
        }
        .flow-node {
            background: rgba(30, 41, 59, 0.9);
            border: 1px solid var(--border-color);
            border-radius: 14px;
            padding: 20px;
            width: 190px;
            text-align: center;
            position: relative;
            z-index: 2;
            box-shadow: 0 10px 25px -5px rgba(0,0,0,0.5);
            transition: all 0.3s;
        }
        .flow-node:hover {
            border-color: var(--accent-cyan);
            box-shadow: 0 0 20px rgba(6, 182, 212, 0.3);
            transform: scale(1.03);
        }
        .node-icon { font-size: 24px; margin-bottom: 8px; }
        .node-title { font-weight: 700; font-size: 14px; margin-bottom: 4px; color: #fff; }
        .node-desc { font-size: 11px; color: var(--text-muted); }
        .flow-arrow {
            flex-grow: 1;
            height: 2px;
            background: linear-gradient(90deg, var(--accent-blue), var(--accent-purple));
            position: relative;
            min-width: 40px;
        }
        .flow-arrow::after {
            content: '';
            position: absolute;
            right: 0;
            top: -4px;
            width: 0;
            height: 0;
            border-top: 5px solid transparent;
            border-bottom: 5px solid transparent;
            border-left: 8px solid var(--accent-purple);
        }

        /* Search & Context Simulator */
        .controls-row {
            display: flex;
            gap: 12px;
            margin-bottom: 20px;
        }
        .search-input {
            flex-grow: 1;
            background-color: #0d1322;
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 12px 18px;
            color: #fff;
            font-size: 14px;
            outline: none;
        }
        .search-input:focus { border-color: var(--accent-blue); box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2); }
        .btn {
            background: linear-gradient(135deg, var(--accent-blue), #2563eb);
            color: #fff;
            border: none;
            border-radius: 10px;
            padding: 12px 24px;
            font-weight: 600;
            font-size: 14px;
            cursor: pointer;
            transition: opacity 0.2s;
        }
        .btn:hover { opacity: 0.9; }

        .code-container {
            background-color: #080c14;
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 18px;
            font-family: var(--font-mono);
            font-size: 12px;
            color: #7dd3fc;
            overflow-x: auto;
            max-height: 450px;
            white-space: pre-wrap;
        }

        .compression-bar-container {
            background: #1e293b;
            border-radius: 10px;
            height: 24px;
            width: 100%;
            overflow: hidden;
            margin: 12px 0;
            display: flex;
        }
        .bar-used { background: linear-gradient(90deg, var(--accent-emerald), var(--accent-cyan)); height: 100%; }
        .bar-saved { background: rgba(255,255,255,0.05); height: 100%; flex-grow: 1; }

        /* Tables */
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 12px;
            font-size: 13px;
        }
        th, td {
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }
        th { background-color: rgba(255,255,255,0.02); color: var(--text-muted); font-weight: 600; }
        tr:hover { background-color: rgba(255,255,255,0.02); }
        .path-cell { font-family: var(--font-mono); color: #93c5fd; }
    </style>
</head>
<body>
    <header>
        <div class="logo-group">
            <div class="logo-icon">DP</div>
            <div>
                <h1>DataPipe v2 Visualizer</h1>
                <div class="subtitle">Incremental Multimodal Indexing & AI Context Engine</div>
            </div>
        </div>
        <div class="badge">
            <div class="pulse"></div>
            Engine Active • FTS5 & xxHash WAL Mode
        </div>
    </header>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-label">Pipeline Name</div>
            <div class="stat-value" id="stat-pipe-name">loading...</div>
            <div class="stat-subtext" id="stat-db-path">index.db</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Indexed Files</div>
            <div class="stat-value" id="stat-files">0</div>
            <div class="stat-subtext">Monitored by watchdog</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Total Chunks / Rows</div>
            <div class="stat-value" id="stat-rows">0</div>
            <div class="stat-subtext">BM25 indexed</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Context Compression</div>
            <div class="stat-value" id="stat-compression">85%</div>
            <div class="stat-subtext">Token budget savings</div>
        </div>
    </div>

    <div class="nav-tabs">
        <button class="tab-btn active" onclick="switchTab('flow')">⚡ Pipeline Architecture</button>
        <button class="tab-btn" onclick="switchTab('context')">🧠 Context Window Simulator</button>
        <button class="tab-btn" onclick="switchTab('search')">🔍 Full-Text BM25 Search</button>
        <button class="tab-btn" onclick="switchTab('files')">📁 Monitored Files</button>
        <button class="tab-btn" onclick="switchTab('session')">📜 Session Memory Log</button>
    </div>

    <!-- Tab 1: Architecture Flow -->
    <div id="tab-flow" class="tab-panel active">
        <div class="visualizer-card">
            <h2 style="font-size: 16px; margin-bottom: 8px;">Real-Time Data Pipeline Architecture</h2>
            <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 20px;">
                How DataPipe watches raw files, calculates ultra-fast xxHash deltas, chunks multimodal inputs, and injects context into AI models.
            </p>
            <div class="flow-container">
                <div class="flow-node">
                    <div class="node-icon">📂</div>
                    <div class="node-title">1. Monitored Directory</div>
                    <div class="node-desc">CSV, MD, Py AST, PDF, JSON, DOCX, Images</div>
                </div>
                <div class="flow-arrow"></div>
                <div class="flow-node">
                    <div class="node-icon">⚡</div>
                    <div class="node-title">2. Delta Engine</div>
                    <div class="node-desc">xxHash fingerprinting (~10x faster) + Pandas outer merge</div>
                </div>
                <div class="flow-arrow"></div>
                <div class="flow-node">
                    <div class="node-icon">🧩</div>
                    <div class="node-title">3. Parser Registry</div>
                    <div class="node-desc">libcst AST Python parser + section chunkers</div>
                </div>
                <div class="flow-arrow"></div>
                <div class="flow-node">
                    <div class="node-icon">🗄️</div>
                    <div class="node-title">4. SQLite FTS5 DB</div>
                    <div class="node-desc">Porter stemming & BM25 ranked indexing</div>
                </div>
                <div class="flow-arrow"></div>
                <div class="flow-node" style="border-color: var(--accent-purple);">
                    <div class="node-icon">🤖</div>
                    <div class="node-title">5. AI Context Window</div>
                    <div class="node-desc">MCP / Token-budgeted snapshot for LLM Agents</div>
                </div>
            </div>
        </div>
    </div>

    <!-- Tab 2: Context Window Simulator -->
    <div id="tab-context" class="tab-panel">
        <div class="visualizer-card">
            <h2 style="font-size: 16px; margin-bottom: 12px;">AI Context Window Builder</h2>
            <div class="controls-row">
                <input type="text" id="ctx-query-input" class="search-input" placeholder="Enter query topic (e.g., Python function SQLite delta)..." value="python delta">
                <button class="btn" onclick="buildContext()">Generate Context</button>
            </div>
            
            <div id="ctx-metrics" style="display:none; margin-bottom: 16px;">
                <div style="display: flex; justify-content: space-between; font-size: 13px; font-family: var(--font-mono);">
                    <span>Used Tokens: <strong id="val-used" style="color: var(--accent-cyan)">0</strong> / <span id="val-max">4000</span></span>
                    <span>Raw Unindexed Tokens: <strong id="val-raw" style="color: var(--accent-amber)">0</strong></span>
                    <span>Token Savings: <strong id="val-savings" style="color: var(--accent-emerald)">0%</strong></span>
                </div>
                <div class="compression-bar-container">
                    <div class="bar-used" id="ctx-bar" style="width: 20%;"></div>
                    <div class="bar-saved"></div>
                </div>
            </div>

            <div class="code-container" id="ctx-output">Click "Generate Context" to build the token-budgeted prompt for LLMs...</div>
        </div>
    </div>

    <!-- Tab 3: BM25 Search -->
    <div id="tab-search" class="tab-panel">
        <div class="visualizer-card">
            <h2 style="font-size: 16px; margin-bottom: 12px;">BM25 Full-Text Search</h2>
            <div class="controls-row">
                <input type="text" id="search-query-input" class="search-input" placeholder="Type keywords..." onkeyup="if(event.key==='Enter') executeSearch()">
                <button class="btn" onclick="executeSearch()">Search</button>
            </div>
            <div id="search-results-table"></div>
        </div>
    </div>

    <!-- Tab 4: Monitored Files -->
    <div id="tab-files" class="tab-panel">
        <div class="visualizer-card">
            <h2 style="font-size: 16px; margin-bottom: 12px;">Monitored File Index State</h2>
            <div id="files-table">Loading files...</div>
        </div>
    </div>

    <!-- Tab 5: Session Memory -->
    <div id="tab-session" class="tab-panel">
        <div class="visualizer-card">
            <h2 style="font-size: 16px; margin-bottom: 12px;">Agent Session Resume Snapshot</h2>
            <div class="controls-row">
                <input type="text" id="session-key-input" class="search-input" placeholder="Enter session key..." value="demo-session">
                <button class="btn" onclick="loadSession()">Fetch Snapshot</button>
            </div>
            <div class="code-container" id="session-output">Enter session key and click Fetch Snapshot...</div>
        </div>
    </div>

    <script>
        function switchTab(name) {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById('tab-' + name).classList.add('active');
        }

        async function fetchStats() {
            const res = await fetch('/api/stats');
            const data = await res.json();
            document.getElementById('stat-pipe-name').innerText = data.pipeline_name || 'datapipe';
            document.getElementById('stat-db-path').innerText = data.db_path || 'index.db';
            document.getElementById('stat-files').innerText = data.file_count || 0;
            document.getElementById('stat-rows').innerText = data.total_rows || 0;
        }

        async function buildContext() {
            const q = document.getElementById('ctx-query-input').value;
            const res = await fetch(`/api/context?q=${encodeURIComponent(q)}&max_tokens=4000`);
            const data = await res.json();
            
            document.getElementById('ctx-metrics').style.display = 'block';
            document.getElementById('val-used').innerText = data.used_tokens;
            document.getElementById('val-max').innerText = data.max_tokens;
            document.getElementById('val-raw').innerText = data.raw_estimated_tokens;
            document.getElementById('val-savings').innerText = data.token_savings_pct + '%';
            document.getElementById('stat-compression').innerText = data.token_savings_pct + '%';
            
            const pct = Math.min(100, Math.round((data.used_tokens / data.max_tokens) * 100));
            document.getElementById('ctx-bar').style.width = pct + '%';
            
            document.getElementById('ctx-output').innerText = data.formatted_text;
        }

        async function executeSearch() {
            const q = document.getElementById('search-query-input').value;
            const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
            const data = await res.json();
            const container = document.getElementById('search-results-table');
            
            if (!data.results || data.results.length === 0) {
                container.innerHTML = '<div style="color:var(--text-muted); padding:16px;">No matching records found.</div>';
                return;
            }
            
            let html = '<table><thead><tr><th>#</th><th>Source File</th><th>BM25 Rank</th><th>Data Payload</th></tr></thead><tbody>';
            data.results.forEach((r, i) => {
                const src = r._source_path || 'unknown';
                const rank = (r._rank !== undefined) ? Number(r._rank).toFixed(4) : '-';
                delete r._source_path;
                delete r._rank;
                html += `<tr><td>${i+1}</td><td class="path-cell">${src}</td><td>${rank}</td><td><code>${JSON.stringify(r)}</code></td></tr>`;
            });
            html += '</tbody></table>';
            container.innerHTML = html;
        }

        async function loadFiles() {
            const res = await fetch('/api/files');
            const data = await res.json();
            const container = document.getElementById('files-table');
            
            if (!data.files || data.files.length === 0) {
                container.innerHTML = '<div style="color:var(--text-muted); padding:16px;">No files indexed yet.</div>';
                return;
            }
            
            let html = '<table><thead><tr><th>Path</th><th>Type</th><th>Hash (xxh64)</th><th>Rows Indexed</th><th>Last Modified</th></tr></thead><tbody>';
            data.files.forEach(f => {
                const dateStr = new Date(f.mtime * 1000).toLocaleString();
                html += `<tr><td class="path-cell">${f.file_path}</td><td><span style="background:#1e293b;padding:2px 8px;border-radius:4px;">${f.file_type}</span></td><td><code>${f.content_hash.substring(0, 12)}...</code></td><td>${f.row_count}</td><td>${dateStr}</td></tr>`;
            });
            html += '</tbody></table>';
            container.innerHTML = html;
        }

        async function loadSession() {
            const key = document.getElementById('session-key-input').value;
            const res = await fetch(`/api/session?key=${encodeURIComponent(key)}`);
            const data = await res.json();
            document.getElementById('session-output').innerText = data.snapshot || 'No session activity recorded for key.';
        }

        // Init page
        fetchStats();
        loadFiles();
        buildContext();
    </script>
</body>
</html>
"""


class WebUIHandler(BaseHTTPRequestHandler):
    pipeline: "Pipeline"

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query_params = urllib.parse.parse_qs(parsed.query)

        if path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
            return

        if path == "/api/stats":
            s = self.pipeline.stats()
            data = {
                "pipeline_name": self.pipeline.name,
                "db_path": str(self.pipeline.store.db_path),
                "file_count": s.get("file_count", 0),
                "total_rows": s.get("total_rows", 0),
            }
            self._send_json(data)
            return

        if path == "/api/files":
            files = self.pipeline.store.all_file_states(self.pipeline.name)
            self._send_json({"files": files})
            return

        if path == "/api/search":
            q = query_params.get("q", [""])[0]
            df = self.pipeline.search(q, limit=30)
            results = df.to_dict(orient="records") if not df.empty else []
            self._send_json({"query": q, "results": results})
            return

        if path == "/api/context":
            from datapipe.context import ContextBuilder
            q = query_params.get("q", [""])[0]
            max_tokens = int(query_params.get("max_tokens", [4000])[0])
            ctx = ContextBuilder(self.pipeline).build_context(q, max_tokens=max_tokens)
            self._send_json(ctx)
            return

        if path == "/api/session":
            key = query_params.get("key", [""])[0]
            from datapipe.memory import SessionMemory
            mem = SessionMemory(self.pipeline.store)
            snap = mem.get_resume_snapshot(key)
            self._send_json({"session_key": key, "snapshot": snap})
            return

        self.send_response(404)
        self.end_headers()

    def _send_json(self, data: Any) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode("utf-8"))

    def log_message(self, format: str, *args: Any) -> None:
        # Suppress noisy HTTP request logging in CLI console
        pass


def launch_webui(pipeline: "Pipeline", port: int = 8500, open_browser: bool = True) -> None:
    handler = type("ConfiguredUIHandler", (WebUIHandler,), {"pipeline": pipeline})
    server = HTTPServer(("0.0.0.0", port), handler)
    url = f"http://localhost:{port}"
    print(f"\n[datapipe] Web UI Visualizer launched at: {url}")
    print("[datapipe] Press Ctrl+C to stop the Web UI server.")
    
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[datapipe] Stopping Web UI server...")
        server.server_close()
