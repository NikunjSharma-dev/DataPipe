from datapipe import Pipeline, Store

store = Store("datapipe.db")
pipe = Pipeline(
    store=store,
    source_dirs=["data", "examples"],
    session_id="hackathon-session-001"
)
