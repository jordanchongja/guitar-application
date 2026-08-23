"""
modules/database.py

Persistence layer for the Progress Dashboard: practice-session logs and quiz
scores. Two backends share the same public API below (log_practice,
log_quiz_score, get_practice_last_n_days, get_recent_quiz_scores,
get_practice_summary) so no page needs to know or care which one is active:

- Google Sheets, when `st.secrets["gcp_service_account"]` and
  `st.secrets["gsheet"]["spreadsheet_id"]` are configured. This is the
  durable option -- use it once the app is deployed, since a hosted
  Streamlit instance's local filesystem is not guaranteed to survive
  redeploys or idle recycling.
- A local SQLite file (`guitar_app.db`), used automatically whenever those
  secrets aren't present. Zero setup, but the file only persists on your
  own machine's disk -- fine for local development, not for a hosted app.

See README.md for the one-time Google Sheets setup steps (service account,
sharing the sheet, secrets.toml contents).
"""

from __future__ import annotations

import datetime as dt
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).resolve().parent.parent / "guitar_app.db"

PRACTICE_HEADERS = ["date", "duration_minutes", "focus_area"]
QUIZ_HEADERS = ["date", "quiz_name", "score", "total"]

_SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _sheets_configured() -> bool:
    # st.secrets raises StreamlitSecretNotFoundError -- not just "falsy" --
    # when no secrets.toml exists anywhere, which is the normal state for a
    # fresh local checkout. Any failure here just means "no Sheets config",
    # so fall back to SQLite rather than crashing the app.
    try:
        return "gcp_service_account" in st.secrets and "gsheet" in st.secrets
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Google Sheets backend
# ---------------------------------------------------------------------------

@st.cache_resource
def _get_spreadsheet():
    import gspread
    from google.oauth2.service_account import Credentials

    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]), scopes=_SHEETS_SCOPES
    )
    gc = gspread.authorize(creds)
    return gc.open_by_key(st.secrets["gsheet"]["spreadsheet_id"])


@st.cache_resource
def _get_worksheet(name: str, headers: tuple[str, ...]):
    import gspread

    sh = _get_spreadsheet()
    try:
        return sh.worksheet(name)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=name, rows=2000, cols=len(headers))
        ws.append_row(list(headers))
        return ws


@st.cache_data(ttl=30, show_spinner=False)
def _sheets_practice_rows() -> list[dict]:
    return _get_worksheet("practice_logs", tuple(PRACTICE_HEADERS)).get_all_records()


@st.cache_data(ttl=30, show_spinner=False)
def _sheets_quiz_rows() -> list[dict]:
    return _get_worksheet("quiz_scores", tuple(QUIZ_HEADERS)).get_all_records()


def _sheets_log_practice(duration_minutes: int, focus_area: str, date: str) -> None:
    _get_worksheet("practice_logs", tuple(PRACTICE_HEADERS)).append_row([date, duration_minutes, focus_area])
    _sheets_practice_rows.clear()


def _sheets_log_quiz_score(quiz_name: str, score: int, total: int, date: str) -> None:
    _get_worksheet("quiz_scores", tuple(QUIZ_HEADERS)).append_row([date, quiz_name, score, total])
    _sheets_quiz_rows.clear()


# ---------------------------------------------------------------------------
# SQLite backend (local fallback)
# ---------------------------------------------------------------------------

def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _sqlite_init_db() -> None:
    with _get_connection() as conn:
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


def _sqlite_log_practice(duration_minutes: int, focus_area: str, date: str) -> None:
    with _get_connection() as conn:
        conn.execute(
            "INSERT INTO practice_logs (date, duration_minutes, focus_area) VALUES (?, ?, ?)",
            (date, duration_minutes, focus_area),
        )
        conn.commit()


def _sqlite_log_quiz_score(quiz_name: str, score: int, total: int, date: str) -> None:
    with _get_connection() as conn:
        conn.execute(
            "INSERT INTO quiz_scores (date, quiz_name, score, total) VALUES (?, ?, ?, ?)",
            (date, quiz_name, score, total),
        )
        conn.commit()


def _sqlite_practice_rows() -> list[dict]:
    with _get_connection() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT date, duration_minutes, focus_area FROM practice_logs ORDER BY id").fetchall()
        return [dict(r) for r in rows]


def _sqlite_quiz_rows() -> list[dict]:
    with _get_connection() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT date, quiz_name, score, total FROM quiz_scores ORDER BY id").fetchall()
        return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Public API -- backend-agnostic from here down
# ---------------------------------------------------------------------------

def init_db() -> None:
    if not _sheets_configured():
        _sqlite_init_db()
    # The Sheets backend creates its worksheets lazily on first read/write
    # (see _get_worksheet), so there's nothing to eagerly set up here.


def log_practice(duration_minutes: int, focus_area: str, date: str | None = None) -> None:
    date = date or dt.date.today().isoformat()
    if _sheets_configured():
        _sheets_log_practice(duration_minutes, focus_area, date)
    else:
        _sqlite_log_practice(duration_minutes, focus_area, date)


def log_quiz_score(quiz_name: str, score: int, total: int, date: str | None = None) -> None:
    date = date or dt.date.today().isoformat()
    if _sheets_configured():
        _sheets_log_quiz_score(quiz_name, score, total, date)
    else:
        _sqlite_log_quiz_score(quiz_name, score, total, date)


def _practice_rows() -> list[dict]:
    return _sheets_practice_rows() if _sheets_configured() else _sqlite_practice_rows()


def _quiz_rows() -> list[dict]:
    return _sheets_quiz_rows() if _sheets_configured() else _sqlite_quiz_rows()


def get_practice_last_n_days(n: int = 7) -> pd.DataFrame:
    rows = _practice_rows()
    start_date = (dt.date.today() - dt.timedelta(days=n - 1)).isoformat()

    df = pd.DataFrame(rows, columns=PRACTICE_HEADERS)
    if not df.empty:
        df["duration_minutes"] = pd.to_numeric(df["duration_minutes"], errors="coerce").fillna(0)
        df = df[df["date"] >= start_date]
        df = df.groupby("date", as_index=False)["duration_minutes"].sum()
        df = df.rename(columns={"duration_minutes": "minutes"})
    else:
        df = pd.DataFrame(columns=["date", "minutes"])

    all_days = pd.date_range(end=dt.date.today(), periods=n).date.astype(str)
    full = pd.DataFrame({"date": all_days}).merge(df, on="date", how="left").fillna(0)
    full["minutes"] = full["minutes"].astype(int)
    full = full.set_index("date")
    return full


def get_recent_quiz_scores(limit: int = 10) -> pd.DataFrame:
    rows = _quiz_rows()
    df = pd.DataFrame(rows, columns=QUIZ_HEADERS)
    if df.empty:
        return df
    for col in ("score", "total"):
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    # Both backends append in chronological order, so the most recent entries
    # are the last rows -- reverse to match the old "most recent first" order.
    return df.tail(limit).iloc[::-1].reset_index(drop=True)


def get_practice_summary() -> dict:
    rows = _practice_rows()
    df = pd.DataFrame(rows, columns=PRACTICE_HEADERS)
    if df.empty:
        return {"total_minutes": 0, "days_practiced": 0}
    df["duration_minutes"] = pd.to_numeric(df["duration_minutes"], errors="coerce").fillna(0)
    return {
        "total_minutes": int(df["duration_minutes"].sum()),
        "days_practiced": int(df["date"].nunique()),
    }


# In a Streamlit multipage app, a user can land directly on any page (sidebar
# nav, bookmark, refresh) without ever running main.py first. Running this
# once at import time -- instead of relying on each page to call it -- means
# the SQLite tables always exist no matter which page opens first, whenever
# that's the active backend.
init_db()
