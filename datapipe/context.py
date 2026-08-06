"""
datapipe/context.py — AI Context Window Formatter & Token Optimizer.

Converts full-text search results and session state into formatted,
token-budgeted context blocks ready for LLM prompt injection.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datapipe.engine import Pipeline


def estimate_tokens(text: str) -> int:
    """Rough token estimation (approx 4 characters per token)."""
    return max(1, len(text) // 4)


class ContextBuilder:
    """
    Formats pipeline search results and session memory into a compact,
    high-density context string optimized for AI prompt windows.
    """

    def __init__(self, pipeline: "Pipeline") -> None:
        self.pipeline = pipeline

    def build_context(
        self,
        query: str,
        max_tokens: int = 4000,
        session_key: str | None = None,
        limit: int = 15,
    ) -> dict[str, Any]:
        """
        Search the index and assemble a token-bounded context block.
        
        Returns:
            dict containing:
            - formatted_text: Ready-to-inject string for LLM system/user prompt
            - used_tokens: Estimated token count of formatted_text
            - raw_tokens_equivalent: Estimated tokens if full raw files were sent
            - token_savings_pct: Percentage of context tokens saved
            - source_count: Number of chunks included
            - sources: List of source file paths included
        """
        results = self.pipeline.search(query, limit=limit)
        
        context_parts: list[str] = []
        context_parts.append(f"<context_query>{query}</context_query>")
        
        # Add session snapshot if requested
        if session_key:
            from datapipe.memory import SessionMemory
            mem = SessionMemory(self.pipeline.store)
            snapshot = mem.get_resume_snapshot(session_key)
            if snapshot:
                context_parts.append(f"<session_memory>\n{snapshot}\n</session_memory>")

        context_parts.append("<search_results>")
        
        current_tokens = estimate_tokens("\n".join(context_parts))
        sources_included = []
        raw_chars_total = 0

        if not results.empty:
            for idx, row in results.iterrows():
                src_path = row.get("_source_path", "unknown")
                rank = row.get("_rank", 0.0)
                
                # Exclude metadata columns to build payload
                data = {
                    k: v for k, v in row.items() 
                    if not k.startswith("_") and pd_not_null(v)
                }
                
                payload_str = json.dumps(data, ensure_ascii=False)
                chunk_block = (
                    f'  <result index="{idx+1}" source="{src_path}" bm25_rank="{rank:.4f}">\n'
                    f'    {payload_str}\n'
                    f'  </result>'
                )
                
                chunk_tokens = estimate_tokens(chunk_block)
                raw_chars_total += len(payload_str) * 3  # simulate full file context size

                if current_tokens + chunk_tokens > max_tokens:
                    break

                context_parts.append(chunk_block)
                current_tokens += chunk_tokens
                if src_path not in sources_included:
                    sources_included.append(src_path)

        context_parts.append("</search_results>")
        formatted_text = "\n".join(context_parts)
        used_tokens = estimate_tokens(formatted_text)
        
        # Calculate context compression metric
        raw_estimated_tokens = max(used_tokens, (raw_chars_total // 4) + 1000)
        savings_pct = max(0.0, round((1 - (used_tokens / raw_estimated_tokens)) * 100, 1))

        return {
            "formatted_text": formatted_text,
            "used_tokens": used_tokens,
            "max_tokens": max_tokens,
            "raw_estimated_tokens": raw_estimated_tokens,
            "token_savings_pct": savings_pct,
            "source_count": len(sources_included),
            "sources": sources_included,
        }


def pd_not_null(val: Any) -> bool:
    try:
        import pandas as pd
        return pd.notna(val)
    except Exception:
        return val is not None
