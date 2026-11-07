"""
modules/practice.py

Logic shared by the Practice and Pathway pages: loading the map and songs, the "ready to start"
and "getting rusty" signals, and saving a session (updates every item you touched, appends the
session, and also adds the minutes to the running practice total).
"""

from __future__ import annotations

import datetime as dt
import json

from modules import practice_store as store
from modules.database import log_practice
from modules.pathway_seed import SONG_STATUSES, STATUSES, seed_rows

RUSTY_DAYS = 30          # comfortable/solid things untouched this long
STALLED_DAYS = 21        # things you're working on but haven't touched in a while
ACTIVE_STATUSES = {"Working on", "Learning", "Polishing"}


def _date(s: str) -> dt.date | None:
    try:
        return dt.date.fromisoformat(str(s)[:10])
    except ValueError:
        return None


def days_since(s: str, today: dt.date | None = None) -> int | None:
    d = _date(s)
    return ((today or store.now().date()) - d).days if d else None


def ago(s: str) -> str:
    n = days_since(s)
    if n is None:
        return "never"
    return "today" if n == 0 else "yesterday" if n == 1 else f"{n} days ago"


# ----------------------------------------------------------------------------- loading
def pathway() -> list[dict]:
    rows = store.read("pathway")
    if not rows:                                   # first run: plant the starter map
        rows = seed_rows()
        store.write_all("pathway", rows)
        rows = store.read("pathway")
    for r in rows:     # rows saved before the pages folder was renamed
        if r["tool"].startswith("pages/"):
            r["tool"] = "app_" + r["tool"]
    return sorted(rows, key=lambda r: (r["branch"], float(r["order"] or 0)))


def songs() -> list[dict]:
    return store.read("songs")


def catalog() -> dict[str, dict]:
    """Everything you can practise, keyed by id: {'label', 'kind', 'row'}."""
    out = {}
    for r in pathway():
        out[r["id"]] = {"label": r["name"], "kind": r["branch"], "row": r}
    for r in songs():
        out[r["id"]] = {"label": f"{r['title']}" + (f" – {r['artist']}" if r["artist"] else ""),
                        "kind": "Song", "row": r}
    return out


def in_progress() -> list[dict]:
    items = [r | {"_label": r["name"], "_kind": r["branch"]} for r in pathway() if r["status"] == "Working on"]
    items += [r | {"_label": r["title"], "_kind": "Song"} for r in songs() if r["status"] in ACTIVE_STATUSES]
    return sorted(items, key=lambda r: r["last_practiced"] or "", reverse=True)


def wishlist() -> list[dict]:
    return [r | {"_label": r["title"], "_kind": "Song"} for r in songs() if r["status"] == "Wishlist"]


def rusty() -> list[dict]:
    out = []
    for r in pathway():
        n = days_since(r["last_practiced"])
        if r["status"] in ("Comfortable", "Solid") and n is not None and n >= RUSTY_DAYS:
            out.append(r | {"_label": r["name"], "_kind": r["branch"], "_days": n})
        elif r["status"] == "Working on" and n is not None and n >= STALLED_DAYS:
            out.append(r | {"_label": r["name"], "_kind": r["branch"], "_days": n})
    for r in songs():
        n = days_since(r["last_practiced"])
        if r["status"] in ("Learned", "Polishing", "Learning") and n is not None and n >= RUSTY_DAYS:
            out.append(r | {"_label": r["title"], "_kind": "Song", "_days": n})
    return sorted(out, key=lambda r: -r["_days"])


def ready_to_start(rows: list[dict]) -> set[str]:
    """Ids of not-started items whose previous item in the branch is comfortable or better
    (or that are first in their branch)."""
    ready, by_branch = set(), {}
    for r in rows:
        by_branch.setdefault(r["branch"], []).append(r)
    for items in by_branch.values():
        items.sort(key=lambda r: float(r["order"] or 0))
        for i, r in enumerate(items):
            if r["status"] != "Not started":
                continue
            prev_ok = i == 0 or items[i - 1]["status"] in ("Comfortable", "Solid")
            if prev_ok:
                ready.add(r["id"])
    return ready


# ----------------------------------------------------------------------------- sessions
def sessions() -> list[dict]:
    return sorted(store.read("sessions"), key=lambda r: r["start"], reverse=True)


def session_items() -> list[dict]:
    return store.read("session_items")


def active_session() -> dict | None:
    return store.get_state("active_session")


def start_session() -> None:
    store.set_state("active_session", {"start": store.now().isoformat(), "items": []})


def set_active_items(item_ids: list[str]) -> None:
    s = active_session()
    if s is not None:
        s["items"] = item_ids
        store.set_state("active_session", s)


def tempo_history(item_id: str, limit: int = 8) -> list[tuple[str, int]]:
    """[(date, bpm), ...] oldest first, from every session where you logged a tempo for this item."""
    pts = []
    for r in store.read("session_items"):
        if r["item_id"] == item_id and str(r.get("bpm", "")).strip():
            try:
                pts.append((r["date"], int(float(r["bpm"]))))
            except ValueError:
                pass
    pts.sort()
    return pts[-limit:]


def parse_song_link(url: str) -> tuple[str, str]:
    """Title and artist from an Ultimate Guitar link, e.g.
    tabs.ultimate-guitar.com/tab/the-black-skirts/everything-chords-2378943 -> ('Everything', 'The Black Skirts')."""
    import re

    m = re.search(r"ultimate-guitar\.com/tab/([^/]+)/([^/?#]+)", url or "")
    if not m:
        return "", ""
    artist = m.group(1).replace("-", " ").title()
    slug = re.sub(r"-(chords|tabs?|ukulele|bass|power|guitar-pro|official|video)(-\d+)?$", "", m.group(2))
    slug = re.sub(r"-\d+$", "", slug)
    slug = re.sub(r"-(chords|tabs?|official)$", "", slug)
    return slug.replace("-", " ").title(), artist


def add_song(title: str, artist: str = "", url: str = "", status: str = "Learning", key: str = "",
             capo: str = "") -> str:
    """Create a song in the catalogue and return its id (reuses an existing song with the same title)."""
    rows = songs()
    for s in rows:
        if s["title"].strip().lower() == title.strip().lower():
            return s["id"]
    nums = [int(s["id"][4:]) for s in rows if s["id"].startswith("song") and s["id"][4:].isdigit()]
    sid = f"song{max(nums + [0]) + 1}"
    store.append("songs", {"id": sid, "title": title.strip(), "artist": artist.strip(), "url": url.strip(),
                           "key": key, "capo": capo, "status": status, "added": store.now().date().isoformat()})
    return sid


def fmt_clock(secs: int) -> str:
    h, rem = divmod(max(secs, 0), 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def elapsed_seconds(s: dict) -> int:
    """Seconds actually practised in the running session (paused time excluded)."""
    now = store.now()
    total = (now - dt.datetime.fromisoformat(s["start"])).total_seconds()
    paused = float(s.get("paused_secs", 0))
    if s.get("paused_at"):
        paused += (now - dt.datetime.fromisoformat(s["paused_at"])).total_seconds()
    return max(0, int(total - paused))


def pause_session() -> None:
    s = active_session()
    if s is not None and not s.get("paused_at"):
        s["paused_at"] = store.now().isoformat()
        store.set_state("active_session", s)


def resume_session() -> None:
    s = active_session()
    if s is not None and s.get("paused_at"):
        s["paused_secs"] = float(s.get("paused_secs", 0)) + (
            store.now() - dt.datetime.fromisoformat(s["paused_at"])).total_seconds()
        s["paused_at"] = None
        store.set_state("active_session", s)


def set_active_field(field: str, value) -> None:
    s = active_session()
    if s is not None and s.get(field) != value:
        s[field] = value
        store.set_state("active_session", s)


def set_active_notes(text: str) -> None:
    s = active_session()
    if s is not None and s.get("notes", "") != text:
        s["notes"] = text
        store.set_state("active_session", s)


def cancel_session() -> None:
    store.set_state("active_session", None)


def save_session(start: dt.datetime, minutes: int, updates: dict[str, dict], notes: str = "",
                 recording: str = "") -> None:
    """updates: {item_id: {'status': ..., 'note': ..., 'bpm': ...}} for every item touched."""
    cat = catalog()
    sid = start.strftime("%Y%m%d-%H%M%S")
    day = start.date().isoformat()
    end = start + dt.timedelta(minutes=minutes)

    # 1. update the items themselves
    p_rows, s_rows = pathway(), songs()
    for rows, table in ((p_rows, "pathway"), (s_rows, "songs")):
        changed = False
        for r in rows:
            u = updates.get(r["id"])
            if not u:
                continue
            r["last_practiced"] = day
            if u.get("status"):
                r["status"] = u["status"]
            if u.get("note"):
                r["next_note"] = u["note"]
            if u.get("bpm"):
                r["bpm"] = u["bpm"]
            changed = True
        if changed:
            store.write_all(table, rows)

    # 2. the session + one line per item
    store.append("sessions", {"id": sid, "start": start.isoformat(), "end": end.isoformat(),
                              "minutes": minutes, "items": json.dumps(list(updates)),
                              "notes": notes, "recording": recording})
    for item_id, u in updates.items():
        store.append("session_items", {"session_id": sid, "date": day, "item_id": item_id,
                                       "item": cat.get(item_id, {}).get("label", item_id),
                                       "status": u.get("status", ""), "note": u.get("note", ""),
                                       "bpm": u.get("bpm", "")})

    # 3. add to the running total
    kinds = [cat[i]["kind"] for i in updates if i in cat]
    focus = max(set(kinds), key=kinds.count) if kinds else "Other"
    log_practice(int(minutes), f"Session: {focus}", date=day)
    cancel_session()


def delete_session(session_id: str) -> None:
    """Undo a session: remove it, its item lines and its practice total row, and set each item's
    'last practised' back to the latest remaining session that touched it. Statuses and notes you
    set stay as they are (they're easy to change on the Pathway page)."""
    from modules.database import delete_practice_log

    sess = [s for s in store.read("sessions") if s["id"] == session_id]
    if not sess:
        return
    s = sess[0]
    store.write_all("sessions", [x for x in store.read("sessions") if x["id"] != session_id])
    all_items = store.read("session_items")
    touched = {r["item_id"] for r in all_items if r["session_id"] == session_id}
    remaining = [r for r in all_items if r["session_id"] != session_id]
    store.write_all("session_items", remaining)

    latest = {}
    for r in remaining:
        if r["item_id"] in touched and r["date"] > latest.get(r["item_id"], ""):
            latest[r["item_id"]] = r["date"]
    for table in ("pathway", "songs"):
        rows = store.read(table)
        changed = False
        for r in rows:
            if r["id"] in touched:
                r["last_practiced"] = latest.get(r["id"], "")
                changed = True
        if changed:
            store.write_all(table, rows)
    try:
        delete_practice_log(s["start"][:10], int(float(s["minutes"] or 0)))
    except Exception:
        pass


def sheet_url() -> str | None:
    """Link to the Google Sheet behind the app (None when running on local storage)."""
    from modules.database import _sheets_configured
    import streamlit as st

    if not _sheets_configured():
        return None
    return f"https://docs.google.com/spreadsheets/d/{st.secrets['gsheet']['spreadsheet_id']}/edit"


def minutes_by_kind(days: int = 30) -> dict[str, int]:
    """Rough split of recent practice minutes across branches (a session's minutes are shared
    equally between the items touched)."""
    cutoff = (store.now().date() - dt.timedelta(days=days)).isoformat()
    cat = catalog()
    out: dict[str, float] = {}
    for s in store.read("sessions"):
        if s["start"][:10] < cutoff:
            continue
        try:
            ids = json.loads(s["items"] or "[]")
            mins = float(s["minutes"] or 0)
        except (ValueError, json.JSONDecodeError):
            continue
        for i in ids or []:
            kind = cat.get(i, {}).get("kind", "Other")
            out[kind] = out.get(kind, 0) + mins / max(len(ids), 1)
    return {k: round(v) for k, v in out.items()}


def month_recap() -> dict:
    """This month vs last month, plus areas you haven't touched in a while (for the home page)."""
    today = store.now().date()
    this_start = today.replace(day=1)
    last_start = (this_start - dt.timedelta(days=1)).replace(day=1)
    sess = store.read("sessions")
    items = store.read("session_items")

    def in_range(d, a, b):
        return a.isoformat() <= d[:10] < b.isoformat()

    this = [s for s in sess if s["start"][:10] >= this_start.isoformat()]
    last = [s for s in sess if in_range(s["start"], last_start, this_start)]
    mins = lambda ss: round(sum(float(s["minutes"] or 0) for s in ss))
    ids = {s["id"] for s in this}
    cat = catalog()
    touched = [r for r in items if r["session_id"] in ids]
    songs_touched = sorted({r["item"] for r in touched if cat.get(r["item_id"], {}).get("kind") == "Song"})

    # neglected: branches with no tagged practice in 21+ days (only once you've logged something)
    last_by_kind = {}
    for r in items:
        kind = cat.get(r["item_id"], {}).get("kind")
        if kind and kind != "Song" and r["date"] > last_by_kind.get(kind, ""):
            last_by_kind[kind] = r["date"]
    from modules.pathway_seed import BRANCHES
    neglected = []
    if items:
        for b in BRANCHES:
            d = last_by_kind.get(b)
            n = days_since(d) if d else None
            if n is None or n >= 21:
                neglected.append((b, n))
    return {
        "month": this_start.strftime("%B"),
        "minutes": mins(this), "last_minutes": mins(last),
        "sessions": len(this), "days": len({s["start"][:10] for s in this}),
        "songs": songs_touched, "neglected": neglected,
        "last_session": max(sess, key=lambda s: s["start"]) if sess else None,
    }


def streak(days: list[str]) -> int:
    ds = sorted({_date(d) for d in days if _date(d)}, reverse=True)
    today = store.now().date()
    if not ds or (today - ds[0]).days > 1:
        return 0
    n = 1
    for a, b in zip(ds, ds[1:]):
        if (a - b).days == 1:
            n += 1
        else:
            break
    return n


__all__ = ["STATUSES", "SONG_STATUSES"]
