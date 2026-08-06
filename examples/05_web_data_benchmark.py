"""
Example 05 — Web Research Data & Benchmark Demo
=================================================
Indexes real-world LLM context window benchmarks and demonstrates
sub-15ms BM25 context prompt generation.

Usage:
    python3 examples/05_web_data_benchmark.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from datapipe import Pipeline, Store, ContextBuilder, auto_transform

def main():
    store = Store("datapipe_benchmarks.db")
    pipe = (
        Pipeline("web_research", store)
        .source(Path(__file__).parent.parent / "data", patterns=["*.json", "*.md"])
        .transform(auto_transform)
        .columns(["title", "text", "summary", "keywords", "benchmarks"])
    )
    pipe.run()

    print("=== Web Research Benchmark Search Results ===")
    results = pipe.search("RAG vs long context latency", limit=3)
    print(results)

    print("\n=== AI Context Window Generation ===")
    builder = ContextBuilder(pipe)
    ctx = builder.build_context("RAG vs long context latency", max_tokens=1500)
    print(f"Tokens Used    : {ctx['used_tokens']} / {ctx['max_tokens']}")
    print(f"Token Savings  : {ctx['token_savings_pct']}%")
    print("\nFormatted Prompt Payload:")
    print(ctx["formatted_text"][:600] + "...\n")

if __name__ == "__main__":
    main()
