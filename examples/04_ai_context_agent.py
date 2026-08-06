"""
Example 4 — AI Context Window & Session Memory Integration
===========================================================
Demonstrates how an AI Agent / LLM application leverages DataPipe
to retrieve token-budgeted context windows and maintain persistent session memory.

Usage:
    python examples/04_ai_context_agent.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datapipe import Pipeline, Store, ContextBuilder, SessionMemory, auto_transform

def main():
    store = Store("./datapipe_index.db")
    
    # Initialize pipeline
    pipe = (
        Pipeline("ai_knowledge", store)
        .source(Path(__file__).parent / "data", patterns=["*.md", "*.csv"])
        .transform(auto_transform)
        .columns(["section", "text", "title", "body"])
    )
    stats = pipe.run()
    print(f"[1] Pipeline Indexed:\n{stats.summary()}\n")

    # Session Memory Setup
    mem = SessionMemory(store)
    session_key = "hackathon-agent-007"
    mem.ensure_session(session_key)
    mem.log_event(session_key, "agent_init", {"model": "gemini-3.6-flash"}, duration_ms=12)
    mem.log_file_edit(session_key, "data/kb_engineering.md", "updated")

    # Build AI Context Window for an LLM Prompt
    builder = ContextBuilder(pipe)
    ctx = builder.build_context(
        query="database scaling and WAL mode",
        max_tokens=2000,
        session_key=session_key,
    )

    print("=== AI Context Window Output ===")
    print(f"Used Tokens    : {ctx['used_tokens']} / {ctx['max_tokens']}")
    print(f"Token Savings  : {ctx['token_savings_pct']}%")
    print(f"Sources Used   : {ctx['sources']}")
    print("\n--- Formatted Prompt Payload ---")
    print(ctx['formatted_text'])

if __name__ == "__main__":
    main()
