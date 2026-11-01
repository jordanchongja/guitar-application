"""
tools/export_practice.py

Prints the practice tracker tables as JSON (used by the reading sync to mirror your practice into
Obsidian). Reads the same Google Sheet as the app, or practice_data.json when there's no Sheet.

    .venv/Scripts/python.exe tools/export_practice.py
"""

import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TABLES = ["pathway", "songs", "sessions", "session_items"]


def from_sheet(secrets: dict) -> dict:
    import gspread
    from google.oauth2.service_account import Credentials

    creds = Credentials.from_service_account_info(
        dict(secrets["gcp_service_account"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
    sh = gspread.authorize(creds).open_by_key(secrets["gsheet"]["spreadsheet_id"])
    out = {}
    names = {ws.title for ws in sh.worksheets()}
    for t in TABLES:
        if t not in names:
            out[t] = []
            continue
        values = sh.worksheet(t).get_all_values()
        head = values[0] if values else []
        out[t] = [{h: (r[i] if i < len(r) else "") for i, h in enumerate(head)} for r in values[1:]
                  if any(c.strip() for c in r)]
    return out


def main() -> None:
    secrets_path = ROOT / ".streamlit" / "secrets.toml"
    if secrets_path.exists():
        secrets = tomllib.loads(secrets_path.read_text(encoding="utf-8"))
        if "gcp_service_account" in secrets and "gsheet" in secrets:
            data = from_sheet(secrets)
            data["practice_timezone"] = secrets.get("practice_timezone", "Asia/Singapore")
            sys.stdout.reconfigure(encoding="utf-8")
            print(json.dumps(data, ensure_ascii=False))
            return
    local = ROOT / "practice_data.json"
    data = json.loads(local.read_text(encoding="utf-8")) if local.exists() else {}
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps({t: data.get(t, []) for t in TABLES}, ensure_ascii=False))


if __name__ == "__main__":
    main()
