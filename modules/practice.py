"""
modules/practice.py

Logic shared by the Practice and Pathway pages: loading the map and songs, the "ready to start"
and "getting rusty" signals, and saving a session (updates every item you touched, appends the
session, and also logs minutes to the existing Progress Dashboard).
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
                                       "status": u.get("status", ""), "note": u.get("note", "")})

    # 3. keep the existing Progress Dashboard in the loop
    kinds = [cat[i]["kind"] for i in updates if i in cat]
    focus = max(set(kinds), key=kinds.count) if kinds else "Other"
    log_practice(int(minutes), f"Session: {focus}", date=day)
    cancel_session()


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
