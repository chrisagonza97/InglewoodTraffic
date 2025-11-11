import json, sqlite3, pathlib, sys
from datetime import datetime
from dateutil import parser as dtparse
from pytz import timezone
from inglewood_events_cli import collect_events

LA = timezone("America/Los_Angeles")
DB_PATH = pathlib.Path("events.db")

def _iso_la(s: str | None) -> str | None:
    if not s: return None
    d = dtparse.parse(s)
    if d.tzinfo: d = d.astimezone(LA)
    else: d = LA.localize(d)
    return d.isoformat()

def ingest(venue="all", debug=False):
    data = collect_events(venue=venue, debug=debug)
    rows = data["all"]

    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA journal_mode=WAL;")
    cur = con.cursor()

    upsert_sql = """
    INSERT INTO events (venue, title, start_at_la, url, source, first_seen_at, last_seen_at)
    VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
    ON CONFLICT(venue, title, start_date) DO UPDATE SET
      last_seen_at = excluded.last_seen_at,
      start_at_la  = excluded.start_at_la,
      url          = excluded.url,
      source       = excluded.source;
    """
    n = 0
    for ev in rows:
        start_iso = _iso_la(ev.get("start_datetime_local"))
        cur.execute(upsert_sql, (
            ev.get("venue"),
            ev.get("title"),
            start_iso,
            ev.get("url"),
            ev.get("source"),
        ))
        n += 1

    con.commit()
    con.close()
    return {"ingested": n}

if __name__ == "__main__":
    venue = "all"
    debug = "--debug" in sys.argv
    print(ingest(venue=venue, debug=debug))
