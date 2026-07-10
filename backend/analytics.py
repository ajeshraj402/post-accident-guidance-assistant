import clickhouse_connect
from datetime import datetime, timezone
from config import CLICKHOUSE_HOST, CLICKHOUSE_USER, CLICKHOUSE_PASSWORD

_client = None

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS recommendations (
    id              String,
    timestamp       DateTime,
    user_id         String,
    session_id      String,
    state           String,
    repair_cost     Float64,
    deductible      Float64,
    annual_premium  Float64,
    at_fault        UInt8,
    injuries        UInt8,
    prior_claims    UInt8,
    notes           String,
    decision        String,
    confidence      String,
    confidence_score Float64,
    latency_ms      UInt32,
    feedback        Nullable(String)
) ENGINE = MergeTree()
ORDER BY timestamp
"""


def get_client():
    global _client
    if _client is None:
        _client = clickhouse_connect.get_client(
            host=CLICKHOUSE_HOST,
            user=CLICKHOUSE_USER,
            password=CLICKHOUSE_PASSWORD,
            secure=True,
        )
        _client.command(CREATE_TABLE_SQL)
    return _client


def log_recommendation(
    session_id: str,
    user_id: str,
    scenario: dict,
    decision: str,
    confidence: str,
    confidence_score: float,
    latency_ms: int,
) -> None:
    try:
        client = get_client()
        client.insert(
            "recommendations",
            [[
                session_id,
                datetime.now(timezone.utc).replace(tzinfo=None),
                user_id,
                session_id,
                scenario.get("state", ""),
                float(scenario.get("repair_cost", 0)),
                float(scenario.get("deductible", 0)),
                float(scenario.get("annual_premium", 0)),
                int(scenario.get("at_fault", False)),
                int(scenario.get("injuries", False)),
                int(scenario.get("prior_claims_2yr", 0)),
                scenario.get("notes", ""),
                decision,
                confidence,
                float(confidence_score),
                latency_ms,
                None,
            ]],
            column_names=[
                "id", "timestamp", "user_id", "session_id", "state",
                "repair_cost", "deductible", "annual_premium", "at_fault",
                "injuries", "prior_claims", "notes", "decision", "confidence",
                "confidence_score", "latency_ms", "feedback",
            ],
        )
    except Exception as e:
        # Never let analytics failure break the main API response
        print(f"[analytics] logging failed: {e}")


def log_feedback(session_id: str, rating: str) -> None:
    try:
        client = get_client()
        client.command(
            "ALTER TABLE recommendations UPDATE feedback = {rating:String} "
            "WHERE session_id = {session_id:String}",
            parameters={"rating": rating, "session_id": session_id},
        )
    except Exception as e:
        print(f"[analytics] feedback logging failed: {e}")
