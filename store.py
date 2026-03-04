import sqlite3
import json
from datetime import datetime
from typing import List, Optional
from router.models import QueryFeedback, RoutingDecision, ModelTier


DB_PATH = "llm_router.db"


class FeedbackStore:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS routing_decisions (
                    decision_id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    query TEXT,
                    complexity TEXT,
                    domain TEXT,
                    complexity_score REAL,
                    selected_tier TEXT,
                    selected_model TEXT,
                    reasoning TEXT,
                    estimated_cost_usd REAL,
                    tokens_estimated INTEGER
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS query_feedback (
                    feedback_id TEXT PRIMARY KEY,
                    decision_id TEXT,
                    timestamp TEXT,
                    response_quality REAL,
                    user_satisfied INTEGER,
                    required_followup INTEGER,
                    response_length INTEGER,
                    latency_ms REAL,
                    actual_cost_usd REAL,
                    notes TEXT,
                    FOREIGN KEY (decision_id) REFERENCES routing_decisions(decision_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS routing_overrides (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    complexity TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    score_threshold REAL NOT NULL,
                    correct_tier TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    sample_count INTEGER DEFAULT 0
                )
            """)

    def log_decision(self, decision: RoutingDecision):
        with self._conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO routing_decisions
                (decision_id, timestamp, query, complexity, domain, complexity_score,
                 selected_tier, selected_model, reasoning, estimated_cost_usd, tokens_estimated)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    decision.decision_id, decision.timestamp, decision.query,
                    decision.complexity.value, decision.domain.value,
                    decision.complexity_score, decision.selected_tier.value,
                    decision.selected_model, decision.reasoning,
                    decision.estimated_cost_usd, decision.tokens_estimated,
                ),
            )

    def log_feedback(self, feedback: QueryFeedback):
        with self._conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO query_feedback
                (feedback_id, decision_id, timestamp, response_quality, user_satisfied,
                 required_followup, response_length, latency_ms, actual_cost_usd, notes)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    feedback.feedback_id, feedback.decision_id, feedback.timestamp,
                    feedback.response_quality,
                    int(feedback.user_satisfied) if feedback.user_satisfied is not None else None,
                    int(feedback.required_followup), feedback.response_length,
                    feedback.latency_ms, feedback.actual_cost_usd, feedback.notes,
                ),
            )

    def get_low_quality_decisions(self, quality_threshold: float = 0.5) -> List[dict]:
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT rd.*, qf.response_quality, qf.required_followup
                FROM routing_decisions rd
                JOIN query_feedback qf ON rd.decision_id = qf.decision_id
                WHERE qf.response_quality < ?
                ORDER BY qf.timestamp DESC""",
                (quality_threshold,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_feedback_stats(self) -> dict:
        with self._conn() as conn:
            total = conn.execute("SELECT COUNT(*) FROM query_feedback").fetchone()[0]
            avg_quality = conn.execute(
                "SELECT AVG(response_quality) FROM query_feedback"
            ).fetchone()[0] or 0
            by_tier = conn.execute(
                """SELECT rd.selected_tier, AVG(qf.response_quality) as avg_q, COUNT(*) as count
                FROM routing_decisions rd
                JOIN query_feedback qf ON rd.decision_id = qf.decision_id
                GROUP BY rd.selected_tier"""
            ).fetchall()
            followup_rate = conn.execute(
                "SELECT AVG(required_followup) FROM query_feedback"
            ).fetchone()[0] or 0
            return {
                "total_feedback": total,
                "avg_quality": round(avg_quality, 3),
                "quality_by_tier": {row[0]: {"avg_quality": round(row[1], 3), "count": row[2]} for row in by_tier},
                "followup_rate": round(followup_rate, 3),
            }

    def get_all_decisions(self, limit: int = 100) -> List[dict]:
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM routing_decisions ORDER BY timestamp DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_cost_summary(self) -> dict:
        with self._conn() as conn:
            total_estimated = conn.execute(
                "SELECT SUM(estimated_cost_usd) FROM routing_decisions"
            ).fetchone()[0] or 0
            total_actual = conn.execute(
                "SELECT SUM(actual_cost_usd) FROM query_feedback"
            ).fetchone()[0] or 0
            by_tier = conn.execute(
                """SELECT selected_tier, SUM(estimated_cost_usd) as cost, COUNT(*) as count
                FROM routing_decisions GROUP BY selected_tier"""
            ).fetchall()
            return {
                "total_estimated_cost": round(total_estimated, 6),
                "total_actual_cost": round(total_actual, 6),
                "cost_by_tier": {row[0]: {"cost": round(row[1], 6), "count": row[2]} for row in by_tier},
            }
