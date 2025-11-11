\connect inglewood
CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- optional, handy later

CREATE TABLE IF NOT EXISTS events (
  id            BIGSERIAL PRIMARY KEY,
  venue         TEXT NOT NULL,
  title         TEXT NOT NULL,
  start_at_la   TIMESTAMPTZ,            -- timezone-aware, stored in UTC but interpreted correctly
  url           TEXT NOT NULL,
  source        TEXT NOT NULL,
  first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_seen_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  -- The calendar day in LA time for de-dup & queries
  start_date    DATE GENERATED ALWAYS AS ( (start_at_la AT TIME ZONE 'America/Los_Angeles')::date ) STORED
);

-- Natural uniqueness: same (venue, title, LA calendar date)
CREATE UNIQUE INDEX IF NOT EXISTS ux_events_venue_title_day
  ON events(venue, title, start_date);

-- Helpful indexes
CREATE INDEX IF NOT EXISTS ix_events_start_at_la ON events (start_at_la DESC);
CREATE INDEX IF NOT EXISTS ix_events_venue        ON events (venue);
-- for check_db.py
ALTER TABLE public.events OWNER TO ing_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.events TO ing_user;
GRANT USAGE, SELECT ON SEQUENCE public.events_id_seq TO ing_user;
