#!/usr/bin/env python3
import os
from datetime import datetime, date
from typing import List, Optional

import psycopg2
import psycopg2.extras
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from pytz import timezone
from api_middleware import rate_limiter
from fastapi import Request

app = FastAPI(title="Inglewood Events API", version="1.0.0")

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    await rate_limiter.check_rate_limit(client_ip)
    return await call_next(request)

LA = timezone("America/Los_Angeles")
PG_DSN = os.environ["PG_DSN"]  # e.g. postgresql://ing_user:...@db:5432/inglewood

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:8080").split(",")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in ALLOWED_ORIGINS if o.strip()],
    allow_methods=["GET"],
    allow_headers=["*"],
)

class Event(BaseModel):
    venue: str
    title: str
    start_at_la: Optional[datetime]
    start_date: Optional[date]
    url: str
    source: str

def q(sql: str, params: tuple = (), fetch: str = "all"):
    # Connection-per-request: simple, safe for low QPS. Switch to a pool later if needed.
    with psycopg2.connect(PG_DSN) as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, params)
        if fetch == "one":
            row = cur.fetchone()
            return dict(row) if row else None
        if fetch == "val":
            row = cur.fetchone()
            return list(row.values())[0] if row else None
        return [dict(r) for r in cur.fetchall()]

@app.get("/sitemap.xml", response_class=Response)
async def sitemap():
    today = datetime.now().strftime("%Y-%m-%d")
    
    sitemap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://ingl.events/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>"""
    
    return Response(content=sitemap_xml, media_type="application/xml")

@app.get("/healthz")
def healthz():
    last_seen = q("SELECT MAX(last_seen_at) AS last_seen FROM public.events;", fetch="one")["last_seen"]
    count = q("SELECT COUNT(*) AS c FROM public.events;", fetch="one")["c"]
    return {"status": "ok", "rows": count, "last_seen_at": last_seen}

@app.get("/events/upcoming", response_model=List[Event])
def upcoming(limit: int = Query(200, ge=1, le=1000), offset: int = Query(0, ge=0)):
    sql = """
    SELECT venue, title, start_at_la, start_date, url, source
    FROM public.events
    WHERE start_date >= (NOW() AT TIME ZONE 'America/Los_Angeles')::date
    ORDER BY start_at_la NULLS LAST, title
    LIMIT %s OFFSET %s;
    """
    return q(sql, (limit, offset))

@app.get("/events/today", response_model=List[Event])
def today(limit: int = Query(200, ge=1, le=1000), offset: int = Query(0, ge=0)):
    sql = """
    SELECT venue, title, start_at_la, start_date, url, source
    FROM public.events
    WHERE start_date = (NOW() AT TIME ZONE 'America/Los_Angeles')::date
    ORDER BY start_at_la NULLS LAST, title
    LIMIT %s OFFSET %s;
    """
    return q(sql, (limit, offset))

@app.get("/events/by-venue", response_model=List[Event])
def by_venue(venue: str, limit: int = Query(200, ge=1, le=1000), offset: int = Query(0, ge=0)):
    sql = """
    SELECT venue, title, start_at_la, start_date, url, source
    FROM public.events
    WHERE venue = %s
      AND start_date >= (NOW() AT TIME ZONE 'America/Los_Angeles')::date
    ORDER BY start_at_la NULLS LAST, title
    LIMIT %s OFFSET %s;
    """
    return q(sql, (venue, limit, offset))

@app.get("/events/week", response_model=List[Event])
def events_week(
    week_offset: int = Query(0, ge=0, le=52),  # 0=this week, 1=next week, etc.
    limit: int = Query(500, ge=1, le=1000),
    skip: int = Query(0, ge=0),
):
    """
    Returns events in LA-local calendar week:
    - week_offset=0: this week (Mon..Sun)
    - week_offset=1: next week, etc.
    """
    sql = """
    WITH base AS (
      SELECT (NOW() AT TIME ZONE 'America/Los_Angeles')::date AS today
    ),
    wk AS (
      SELECT
        -- Monday of this LA week + N weeks
        (today - EXTRACT(DOW FROM today)::int + 1 + (%s * 7))::date AS start_la,
        -- Next Monday (exclusive end)
        (today - EXTRACT(DOW FROM today)::int + 8 + (%s * 7))::date AS end_la
      FROM base
    )
    SELECT venue, title, start_at_la, start_date, url, source
    FROM public.events, wk
    WHERE start_date >= wk.start_la
      AND start_date <  wk.end_la
    ORDER BY start_at_la NULLS LAST, title
    LIMIT %s OFFSET %s;
    """
    return q(sql, (week_offset, week_offset, limit, skip))