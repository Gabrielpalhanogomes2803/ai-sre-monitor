import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

DB_PATH = Path("/app/data/incidents.db")
LOCAL_TIMEZONE = ZoneInfo("America/Sao_Paulo")


def _to_local_time(value: str) -> str:
    """Converte timestamp ISO UTC para America/Sao_Paulo apenas na apresentação."""
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt.astimezone(LOCAL_TIMEZONE).isoformat()
    except (TypeError, ValueError):
        return value


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS incidents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                alert_name TEXT,
                alert_status TEXT,
                confidence TEXT,
                summary TEXT,
                probable_cause TEXT,
                alert_json TEXT NOT NULL,
                metrics_json TEXT NOT NULL,
                logs_json TEXT NOT NULL,
                analysis_json TEXT NOT NULL
            )
            """
        )
        conn.commit()


def save_incident(alert: dict, metrics: dict, logs: dict, analysis: dict) -> int:
    init_db()

    alert_name = (
        alert.get("commonLabels", {}).get("alertname")
        or alert.get("alert")
        or "Unknown"
    )

    alert_status = (
        alert.get("status")
        or alert.get("state")
        or "unknown"
    )

    created_at = datetime.now(timezone.utc).isoformat()

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            """
            INSERT INTO incidents (
                created_at,
                alert_name,
                alert_status,
                confidence,
                summary,
                probable_cause,
                alert_json,
                metrics_json,
                logs_json,
                analysis_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                alert_name,
                alert_status,
                analysis.get("confidence"),
                analysis.get("summary"),
                analysis.get("probable_cause"),
                json.dumps(alert, ensure_ascii=False),
                json.dumps(metrics, ensure_ascii=False),
                json.dumps(logs, ensure_ascii=False),
                json.dumps(analysis, ensure_ascii=False),
            ),
        )
        conn.commit()
        return cursor.lastrowid


def list_incidents(limit: int = 50):
    init_db()

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            """
            SELECT
                id,
                created_at,
                alert_name,
                alert_status,
                confidence,
                summary,
                probable_cause
            FROM incidents
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    incidents = []

    for row in rows:
        item = dict(row)
        item["created_at"] = _to_local_time(item["created_at"])
        incidents.append(item)

    return incidents


def get_recent_incidents(limit: int = 10):
    init_db()

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            """
            SELECT
                id,
                created_at,
                alert_name,
                alert_status,
                confidence,
                summary,
                probable_cause,
                alert_json,
                metrics_json,
                logs_json,
                analysis_json
            FROM incidents
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    incidents = []

    for row in rows:
        item = dict(row)
        item["created_at"] = _to_local_time(item["created_at"])

        for field in [
            "alert_json",
            "metrics_json",
            "logs_json",
            "analysis_json",
        ]:
            try:
                item[field] = json.loads(item[field])
            except Exception:
                pass

        incidents.append(item)

    return incidents
