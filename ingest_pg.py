import os
import psycopg2
from datetime import datetime
from dateutil import parser as dtparse
from pytz import timezone
from inglewood_events_cli import collect_events

PG_DSN = os.getenv("PG_DSN")  # e.g. postgresql://ing_user:...@db:5432/inglewood
LA = timezone("America/Los_Angeles")

# Retention policy:
#   0  -> keep only today+future (delete past)
#  >0  -> keep last N days of history
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "0"))

def _to_la(iso):
    if not iso: return None
    d = dtparse.parse(iso)
    return d.astimezone(LA) if d.tzinfo else LA.localize(d)

def ingest(venue="all", debug=False):
    data = collect_events(venue=venue, debug=debug)
    rows = data["all"]
    with psycopg2.connect(PG_DSN) as conn, conn.cursor() as cur:
        sql = """
        INSERT INTO events (venue, title, start_at_la, url, source, first_seen_at, last_seen_at)
        VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
        ON CONFLICT (venue, title, start_date)
        DO UPDATE SET
          last_seen_at = EXCLUDED.last_seen_at,
          start_at_la  = EXCLUDED.start_at_la,
          url          = EXCLUDED.url,
          source       = EXCLUDED.source;
        """
        for ev in rows:
            cur.execute(sql, (
                ev.get("venue"),
                ev.get("title"),
                (_to_la(ev.get("start_datetime_local"))
                 if ev.get("start_datetime_local") else None),
                ev.get("url"),
                ev.get("source"),
            ))
        # Optional pruning
        if RETENTION_DAYS == 0:
            cur.execute("""
                DELETE FROM public.events
                WHERE start_date < (NOW() AT TIME ZONE 'America/Los_Angeles')::date
            """)
            print("[prune] removed events before today (LA).")
        elif RETENTION_DAYS > 0:
            # keeping the last N days (LA)
            cur.execute(f"""
                DELETE FROM public.events
                WHERE start_date < ((NOW() AT TIME ZONE 'America/Los_Angeles')::date - INTERVAL '{RETENTION_DAYS} days')
            """)
            print(f"[prune] retained {RETENTION_DAYS} days of history.")

    ts2 = datetime.now(LA).isoformat(timespec="seconds")
    print(f"[{ts2}] ingest complete: processed={len(rows)}")
    return {"ingested": len(rows)}

if __name__ == "__main__":
    print(ingest())
