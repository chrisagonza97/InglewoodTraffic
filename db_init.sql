PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS events (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  venue         TEXT NOT NULL,
  title         TEXT NOT NULL,
  start_at_la   TEXT,              -- ISO8601 string (timezone-aware ok)
  url           TEXT NOT NULL,
  source        TEXT NOT NULL,
  first_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
  last_seen_at  TEXT NOT NULL DEFAULT (datetime('now')),
  -- generated date part for de-dup & queries
  start_date    TEXT GENERATED ALWAYS AS (date(start_at_la)) VIRTUAL
);

-- unique key for upsert: (venue, title, start_date)
CREATE UNIQUE INDEX IF NOT EXISTS ux_events_venue_title_day
  ON events(venue, title, start_date);

CREATE INDEX IF NOT EXISTS ix_events_start_at_la ON events(start_at_la);
CREATE INDEX IF NOT EXISTS ix_events_venue ON events(venue);