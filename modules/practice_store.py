"""
modules/practice_store.py

Storage for the practice tracker (Practice + Pathway pages): the pathway map, songs, sessions,
the running session, and recordings.

Same idea as modules/database.py: Google Sheets when secrets are configured (hosted app),
a local JSON file otherwise. Each table is one worksheet. The tables are small, so edits
rewrite the whole worksheet, which keeps things simple and robust.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import streamlit as st

from modules.database import _get_spreadsheet, _sheets_configured

TABLES: dict[str, list[str]] = {
    "pathway": ["id", "branch", "order", "name", "goal", "how", "tool", "status",
                "last_practiced", "next_note", "bpm"],
    "songs": ["id", "title", "artist", "url", "key", "capo", "status", "last_practiced",
              "next_note", "bpm", "added"],
    "sessions": ["id", "start", "end", "minutes", "items", "notes", "recording"],
    "session_items": ["session_id", "date", "item_id", "item", "status", "note"],
    "practice_state": ["key", "value"],
}

LOCAL_PATH = Path(__file__).resolve().parent.parent / "practice_data.json"


# ----------------------------------------------------------------------------- Sheets
@st.cache_resource
def _ws(name: str):
    import gspread

    sh = _get_spreadsheet()
    try:
        return sh.worksheet(name)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=name, rows=1000, cols=len(TABLES[name]))
        ws.update(values=[TABLES[name]], range_name="A1")
        return ws


@st.cache_data(ttl=60, show_spinner=False)
def _sheet_rows(name: str) -> list[dict]:
    values = _ws(name).get_all_values()
    if not values:
        return []
    headers = values[0]
    return [{h: (row[i] if i < len(row) else "") for i, h in enumerate(headers)} for row in values[1:]
            if any(c.strip() for c in row)]


# ----------------------------------------------------------------------------- local JSON
def _local() -> dict:
    if LOCAL_PATH.exists():
        return json.loads(LOCAL_PATH.read_text(encoding="utf-8"))
    return {}


def _save_local(data: dict) -> None:
    LOCAL_PATH.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")


# ----------------------------------------------------------------------------- public API
def read(name: str) -> list[dict]:
    """All rows of a table as dicts of strings (columns in TABLES order)."""
    cols = TABLES[name]
    rows = _sheet_rows(name) if _sheets_configured() else _local().get(name, [])
    return [{c: str(r.get(c, "") if r.get(c) is not None else "") for c in cols} for r in rows]


def write_all(name: str, rows: list[dict]) -> None:
    cols = TABLES[name]
    clean = [{c: "" if r.get(c) is None else str(r.get(c)) for c in cols} for r in rows]
    if _sheets_configured():
        ws = _ws(name)
        ws.clear()
        ws.update(values=[cols] + [[r[c] for c in cols] for r in clean], range_name="A1")
        _sheet_rows.clear()
    else:
        data = _local()
        data[name] = clean
        _save_local(data)


def append(name: str, row: dict) -> None:
    cols = TABLES[name]
    if _sheets_configured():
        _ws(name).append_row(["" if row.get(c) is None else str(row.get(c)) for c in cols],
                             value_input_option="RAW")
        _sheet_rows.clear()
    else:
        data = _local()
        data.setdefault(name, []).append({c: "" if row.get(c) is None else str(row.get(c)) for c in cols})
        _save_local(data)


def get_state(key: str, default=None):
    for r in read("practice_state"):
        if r["key"] == key:
            try:
                return json.loads(r["value"])
            except json.JSONDecodeError:
                return default
    return default


def set_state(key: str, value) -> None:
    rows = [r for r in read("practice_state") if r["key"] != key]
    if value is not None:
        rows.append({"key": key, "value": json.dumps(value)})
    write_all("practice_state", rows)


def now() -> dt.datetime:
    """Wall-clock time in the practice timezone (secrets: practice_timezone, default Asia/Singapore)."""
    from zoneinfo import ZoneInfo

    try:
        tz = st.secrets.get("practice_timezone", "Asia/Singapore")
    except Exception:
        tz = "Asia/Singapore"
    return dt.datetime.now(ZoneInfo(tz)).replace(tzinfo=None, microsecond=0)


# ----------------------------------------------------------------------------- password
def _secret(key: str, default=None):
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


def unlocked() -> bool:
    """True if this browser may log/edit. Without a Sheet (pure local use) it's open; with your
    Sheet connected, a password is required, so the public app can't touch your data."""
    pw = _secret("app_password")
    if not pw:
        return not _sheets_configured()
    return st.session_state.get("practice_unlocked", False)


def password_gate(where: str = "main") -> bool:
    """Show a password box when locked. Returns True once unlocked."""
    if unlocked():
        return True
    if not _secret("app_password"):
        st.warning("Logging is locked: add `app_password = \"...\"` to this app's secrets to use it.",
                   icon=":material/lock:")
        return False
    box = st.sidebar if where == "sidebar" else st
    with box.form(f"pw_{where}", border=True):
        st.markdown(":material/lock: **Your practice log is private.** Enter the password to log and edit.")
        pw = st.text_input("Password", type="password")
        if st.form_submit_button("Unlock", type="primary"):
            if pw == _secret("app_password"):
                st.session_state.practice_unlocked = True
                st.rerun()
            else:
                st.error("Wrong password.")
    return False


# ----------------------------------------------------------------------------- recordings
def upload_recording(data: bytes, filename: str, mime: str = "audio/wav") -> str:
    """Save a take. Hosted: Google Drive folder (secrets: recordings_folder_id). Local: ./recordings/.
    Returns a link/path. Raises RuntimeError with a readable message on failure."""
    # Preferred: a small Apps Script web app that runs as you and saves into your Drive
    # (service accounts can't own files in a personal Drive). See tools/recordings_apps_script.gs.
    script_url = _secret("recordings_script_url")
    if script_url:
        import base64

        import requests

        try:
            r = requests.post(script_url, timeout=90, json={
                "token": _secret("recordings_token", ""), "name": filename, "mime": mime,
                "data": base64.b64encode(data).decode()})
            res = r.json()
        except Exception as e:
            raise RuntimeError(f"Couldn't reach the recordings script ({e}).")
        if res.get("error") or not res.get("url"):
            raise RuntimeError(f"The recordings script said: {res.get('error', 'no link returned')}")
        return res["url"]

    folder = _secret("recordings_folder_id")
    if not (_sheets_configured() and folder):
        out = Path(__file__).resolve().parent.parent / "recordings"
        out.mkdir(exist_ok=True)
        (out / filename).write_bytes(data)
        return str(out / filename)

    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.service_account import Credentials

    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]), scopes=["https://www.googleapis.com/auth/drive"])
    s = AuthorizedSession(creds)
    meta = json.dumps({"name": filename, "parents": [folder]}).encode()
    body = (b"--rec\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n" + meta +
            b"\r\n--rec\r\nContent-Type: " + mime.encode() + b"\r\n\r\n" + data + b"\r\n--rec--")
    r = s.post("https://www.googleapis.com/upload/drive/v3/files"
               "?uploadType=multipart&supportsAllDrives=true&fields=id,webViewLink",
               data=body, headers={"Content-Type": "multipart/related; boundary=rec"}, timeout=60)
    if not r.ok:
        msg = r.json().get("error", {}).get("message", r.text[:200]) if r.headers.get(
            "content-type", "").startswith("application/json") else r.text[:200]
        raise RuntimeError(f"Couldn't save the recording to Google Drive: {msg}")
    return r.json().get("webViewLink") or f"https://drive.google.com/file/d/{r.json()['id']}/view"
