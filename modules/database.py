"""
modules/database.py

SQLite persistence layer for the Progress Dashboard. Stores practice-session
logs and quiz scores in `guitar_app.db` at the project root.
"""

from __future__ import annotations

import datetime as dt
import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).resolve().parent.parent / "guitar_app.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS practice_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL,
                focus_area TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS quiz_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                quiz_name TEXT NOT NULL,
                score INTEGER NOT NULL,
                total INTEGER NOT NULL
            )
            """
        )
        conn.commit()


def log_practice(duration_minutes: int, focus_area: str, date: str | None = None) -> None:
    date = date or dt.date.today().isoformat()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO practice_logs (date, duration_minutes, focus_area) VALUES (?, ?, ?)",
            (date, duration_minutes, focus_area),
        )
        conn.commit()


def log_quiz_score(quiz_name: str, score: int, total: int, date: str | None = None) -> None:
    date = date or dt.date.today().isoformat()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO quiz_scores (date, quiz_name, score, total) VALUES (?, ?, ?, ?)",
            (date, quiz_name, score, total),
        )
        conn.commit()


def get_practice_last_n_days(n: int = 7) -> pd.DataFrame:
    start_date = (dt.date.today() - dt.timedelta(days=n - 1)).isoformat()
    with get_connection() as conn:
        df = pd.read_sql_query(
            """
            SELECT date, SUM(duration_minutes) AS minutes
            FROM practice_logs
            WHERE date >= ?
            GROUP BY date
            ORDER BY date
            """,
            conn,
            params=(start_date,),
        )

    all_days = pd.date_range(end=dt.date.today(), periods=n).date.astype(str)
    full = pd.DataFrame({"date": all_days}).merge(df, on="date", how="left").fillna(0)
    full["minutes"] = full["minutes"].astype(int)
    full = full.set_index("date")
    return full


def get_recent_quiz_scores(limit: int = 10) -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql_query(
            "SELECT date, quiz_name, score, total FROM quiz_scores ORDER BY id DESC LIMIT ?",
            conn,
            params=(limit,),
        )


def get_practice_summary() -> dict:
    with get_connection() as conn:
        cur = conn.execute("SELECT COALESCE(SUM(duration_minutes), 0) FROM practice_logs")
        total_minutes = cur.fetchone()[0]
        cur = conn.execute("SELECT COUNT(DISTINCT date) FROM practice_logs")
        days_practiced = cur.fetchone()[0]
    return {"total_minutes": total_minutes, "days_practiced": days_practiced}
