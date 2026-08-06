"""
DataPipe v2.1 — Incremental multimodal indexing. Python + pandas + SQLite.

Quick start
-----------
>>> from datapipe import Pipeline, Store, ContextBuilder
>>> from datapipe.parsers import auto_transform
>>>
>>> store = Store("./index.db")
>>> pipe = (
...     Pipeline("docs", store)
...     .source("./data", patterns=["*.csv", "*.json", "*.md", "*.py"])
...     .transform(auto_transform)
...     .columns(["text", "chunk_index"])
... )
>>> stats = pipe.run()
>>> print(stats.summary())
>>> df = pipe.search("machine learning Python")
>>> ctx = ContextBuilder(pipe).build_context("machine learning")
"""

from datapipe.engine import FileDelta, IndexStats, Pipeline, SourceFile, Store, compute_delta
from datapipe.parsers import auto_transform, get_parser, PARSER_REGISTRY
from datapipe.watcher import FileWatcher
from datapipe.memory import SessionMemory, log_tool_call
from datapipe.context import ContextBuilder
from datapipe.mcp import MCPServer
from datapipe.webui import launch_webui
from datapipe.transforms import csv_transform, json_transform, text_transform, excel_transform

__all__ = [
    # engine
    "Pipeline", "Store", "SourceFile", "IndexStats", "FileDelta", "compute_delta",
    # parsers & transforms
    "auto_transform", "get_parser", "PARSER_REGISTRY",
    "csv_transform", "json_transform", "text_transform", "excel_transform",
    # watcher
    "FileWatcher",
    # memory
    "SessionMemory", "log_tool_call",
    # AI Context & Tools
    "ContextBuilder", "MCPServer", "launch_webui",
]

__version__ = "2.1.0"
