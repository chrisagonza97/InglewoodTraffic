#!/usr/bin/env python3
# inglewood_events_cli.py — prints BOTH today's events and ALL events.
# Fixes:
#  - Kia Forum: ignore stale years in datetime attr; infer year from visible date.
#  - SoFi/Intuit: broader selectors, try all candidate pages, no early break.

import argparse, json, re, time, os
from datetime import datetime, date
from urllib.parse import urljoin
from urllib.parse import urlparse
import urllib.robotparser as robotparser

import pytz, requests
from bs4 import BeautifulSoup
from dateutil import parser as dtparse

UA = "TrafficEventsBot/1.0 (+https://example.com/contact)"
LA_TZ = pytz.timezone("America/Los_Angeles")

from pathlib import Path
env_file = Path(__file__).parent / ".env.prod"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())


# ---------------- time helpers ----------------
def la_today(s=None) -> date:
    if s: return datetime.strptime(s, "%Y-%m-%d").date()
    return datetime.now(LA_TZ).date()

def to_la(dtlike):
    if not dtlike: return None
    try:
        dt = dtparse.parse(dtlike)
    except Exception:
        return None
    if dt.tzinfo is None: dt = LA_TZ.localize(dt)
    else: dt = dt.astimezone(LA_TZ)
    return dt

def month_abbrev_to_num(s):
    months = {m[:3].upper(): i for i, m in enumerate(
        ["January","February","March","April","May","June","July","August","September","October","November","December"], 1)}
    key = (s or "").strip().upper()[:3]
    return months.get(key)

def infer_year(mon:int, day:int, now_d:date) -> int:
    """Choose current or next year so that the resulting date is >= today and within ~370 days."""
    this = date(now_d.year, mon, day)
    if this >= now_d:
        return now_d.year
    # if already passed this year, assume it's next year's occurrence
    return now_d.year + 1

# ---------------- robots helpers ----------------
class Robots:
    def __init__(self, base, ua=UA):
        self.base = base.rstrip("/")
        self.ua = ua
        self.parser = robotparser.RobotFileParser()
        self.delay = 0
        self.loaded = False
    def load(self):
        url = urljoin(self.base, "/robots.txt")
        try:
            r = requests.get(url, headers={"User-Agent": self.ua}, timeout=12)
        except requests.RequestException:
            return False
        if r.status_code >= 400:
            return False
        self.parser.parse(r.text.splitlines())
        try:
            self.delay = self.parser.crawl_delay(self.ua) or 0
        except Exception:
            self.delay = 0
        self.loaded = True
        return True
    def can(self, path):
        return self.loaded and self.parser.can_fetch(self.ua, urljoin(self.base, path))

def polite_get(url, delay=0, debug=False):
    if delay: time.sleep(delay)
    if debug: print(f"[GET] {url} (delay={delay})")
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=25)
    except requests.RequestException as e:
        if debug: print(f"[ERR] {url} -> {e}")
        return None
    if r.status_code != 200:
        if debug: print(f"[SKIP] {url} -> HTTP {r.status_code}")
        return None
    return r.text

def extract_event_from_detail(detail_html, base_url):
    """Return (start_iso, title_override) from an event detail page."""
    soup = BeautifulSoup(detail_html, "lxml")

    # 1) JSON-LD first
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
        except Exception:
            continue
        nodes = []
        if isinstance(data, dict):
            nodes = [data] + (data.get("@graph") or [])
        elif isinstance(data, list):
            nodes = data
        for node in nodes:
            if not isinstance(node, dict):
                continue
            typ = node.get("@type")
            if typ == "Event" or (isinstance(typ, list) and "Event" in typ):
                start = node.get("startDate") or node.get("startTime")
                title = (node.get("name") or "").strip() or None
                if start:
                    dt = to_la(start)
                    if dt:
                        return (dt.isoformat(), title)

    # 2) Fallbacks: time/date text blocks frequently used on detail pages
    # Look for a <time datetime="..."> or text like "October 23, 2025 • 5:15 PM"
    t = soup.select_one("time[datetime]")
    if t and t.has_attr("datetime"):
        dt = to_la(t["datetime"])
        if dt:
            return (dt.isoformat(), None)

    # Visible text pattern
    textnodes = soup.select("h1, h2, .event-date, .eventDate, .date, .event-meta, .meta, p")
    for n in textnodes:
        txt = n.get_text(" ", strip=True)
        m = re.search(r"([A-Za-z]{3,9})\.?,?\s+(\d{1,2}),?\s+(\d{4}).{0,10}(\d{1,2}:\d{2}\s*[AP]M)", txt)
        if m:
            mon = month_abbrev_to_num(m.group(1))
            day = int(m.group(2))
            year = int(m.group(3))
            ttxt = m.group(4)
            dttm = to_la(f"{year:04d}-{mon:02d}-{day:02d} {ttxt}")
            if dttm:
                return (dttm.isoformat(), None)

    return (None, None)

# ---------------- INTUIT DOME ----------------
def scrape_intuit_all(debug=False):
    """
    Intuit Dome — https://www.intuitdome.com/events/event-schedule
    Strategy:
      1) Try SSR cards (li[class^=eventCategoryCard_]) if present.
      2) Fallback: parse Next.js __NEXT_DATA__ JSON and extract events.
    """
    base = "https://www.intuitdome.com"
    robots = Robots(base)
    if not robots.load():
        if debug: print("[INTUIT] robots unreachable")
        return []
    path = "/events/event-schedule"
    if not robots.can(path):
        if debug: print("[INTUIT] disallowed by robots")
        return []

    html = polite_get(urljoin(base, path), robots.delay, debug)
    if not html:
        return []
    soup = BeautifulSoup(html, "lxml")

    # ---------- 1) SSR DOM attempt ----------
    cards = soup.select('li[class^="eventCategoryCard_"]')
    if debug: print(f"[INTUIT] SSR cards: {len(cards)}")
    out = []
    today_d = datetime.now(LA_TZ).date()

    def build_event(title, mon_name=None, day_str=None, time_str=None, url_hint=None):
        if not title:
            return None
        start = None
        if mon_name and day_str:
            mon = month_abbrev_to_num(mon_name)
            if mon:
                day = int(day_str)
                year = infer_year(mon, day, today_d)
                ttxt = (time_str or "").strip()
                if not re.search(r"\d", ttxt or ""):
                    ttxt = "18:00"
                start = to_la(f"{year:04d}-{mon:02d}-{day:02d} {ttxt}")
        return {
            "venue": "Intuit Dome",
            "title": title,
            "start_datetime_local": start.isoformat() if start else None,
            "url": url_hint or urljoin(base, path),
            "source": urljoin(base, path),
        }

    if cards:
        for i, li in enumerate(cards):
            title_el = li.select_one('[class^="heading_"], [class^="title_"]')
            title = title_el.get_text(strip=True) if title_el else None
            dt_el = li.select_one('div[class^="data_kopy_"]') or li.select_one('[class*="kopy"]')
            dt_text = dt_el.get_text(" ", strip=True) if dt_el else ""
            # "FRI, OCT 24 / 7:30 PM"
            m = re.search(r'\b[A-Za-z]{3,9}\b,\s*([A-Za-z]{3,9})\s+(\d{1,2})(?:\s*/\s*([0-9:\sAPMapm\.]+))?', dt_text)
            mon_name = day_str = time_str = None
            if m:
                mon_name, day_str, time_str = m.group(1), m.group(2), m.group(3)
            else:
                m2 = re.search(r'([A-Za-z]{3,9})\s+(\d{1,2})', dt_text)
                if m2:
                    mon_name, day_str = m2.group(1), m2.group(2)
            link_el = li.select_one("a[href]")
            link = urljoin(base, link_el["href"]) if link_el else urljoin(base, path)
            ev = build_event(title, mon_name, day_str, time_str, link)
            if debug and i < 5:
                print(f"  [INTUIT SSR#{i}] raw='{dt_text}' -> {ev}")
            if ev:
                out.append(ev)
        if out:
            return out

    # ---------- 2) Next.js __NEXT_DATA__ fallback ----------
    script = soup.find("script", id="__NEXT_DATA__", type="application/json")
    if not script or not (script.string or "").strip():
        if debug: print("[INTUIT] __NEXT_DATA__ not found")
        return out

    try:
        payload = json.loads(script.string)
    except Exception as e:
        if debug: print(f"[INTUIT] __NEXT_DATA__ parse error: {e}")
        return out

    # Heuristics: walk dict/list tree and collect items that look like events
    events = []

    def maybe_iso(s):
        return isinstance(s, str) and re.search(r"\d{4}-\d{2}-\d{2}", s)

    def parse_human_dt(txt):
        if not isinstance(txt, str):
            return (None, None, None)
        # "FRI, OCT 24 / 7:30 PM" or "OCT 24 7:30 PM"
        m = re.search(r'([A-Za-z]{3,9})\s+(\d{1,2})(?:[^0-9A-Za-z]+([0-9:\sAPMapm\.]+))?', txt)
        if not m:
            return (None, None, None)
        return (m.group(1), m.group(2), m.group(3))

    def walk(node):
        if isinstance(node, dict):
            # candidate if it has title/name and a date-ish field
            title = node.get("title") or node.get("name") or node.get("eventTitle")
            url_hint = node.get("url") or node.get("link") or node.get("href")
            start = None
            mon_name = day_str = time_str = None

            # check common datetime fields
            for k in ("startDate", "start_time", "start", "date", "datetime", "eventDate", "eventDatetime"):
                v = node.get(k)
                if maybe_iso(v):
                    start = to_la(v)
                    break
                # sometimes nested like {"date":{"start":"..."}} — handled by recursion
                if isinstance(v, str) and not start:
                    # try parse human-friendly "OCT 24 7:30 PM"
                    mon_name, day_str, time_str = parse_human_dt(v)

            # Also check any text-looking field if no date yet
            if not start and (node.get("displayDate") or node.get("subtitle") or node.get("kicker")):
                mon_name, day_str, time_str = parse_human_dt(
                    node.get("displayDate") or node.get("subtitle") or node.get("kicker")
                )

            if title and (start or mon_name and day_str):
                if start:
                    iso = start.isoformat()
                    events.append({"title": str(title).strip(), "iso": iso, "url": url_hint})
                else:
                    events.append({"title": str(title).strip(), "mon": mon_name, "day": day_str, "time": time_str, "url": url_hint})

            # continue walking
            for v in node.values():
                walk(v)

        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(payload)

    if debug:
        print(f"[INTUIT] __NEXT_DATA__ candidates: {len(events)}")

    # Normalize candidates
    norm = []
    for i, e in enumerate(events):
        title = e.get("title")
        url_hint = e.get("url")
        if e.get("iso"):
            norm.append({
                "venue": "Intuit Dome",
                "title": title,
                "start_datetime_local": to_la(e["iso"]).isoformat() if to_la(e["iso"]) else None,
                "url": url_hint or urljoin(base, path),
                "source": urljoin(base, path),
            })
            continue
        mon_name, day_str, time_str = e.get("mon"), e.get("day"), e.get("time")
        ev = build_event(title, mon_name, day_str, time_str, url_hint or urljoin(base, path))
        if ev:
            norm.append(ev)
        if debug and i < 5:
            print(f"  [INTUIT JSON#{i}] {e} -> {ev}")

    # de-dupe by (title, date)
    seen = set()
    out2 = []
    for ev in norm:
        key = (ev["title"], (ev["start_datetime_local"] or "")[:10])
        if key in seen:
            continue
        seen.add(key)
        out2.append(ev)

    if debug: print(f"[INTUIT] normalized: {len(out2)}")
    return out2


# ---------------- SOFI STADIUM ----------------
def scrape_sofi_all(debug=False):
    """
    SoFi Stadium: list page doesn't include date/time server-side.
    Strategy:
      1) Fetch https://www.sofistadium.com/events
      2) For each card, grab the event link.
      3) Fetch the detail page and parse JSON-LD Event.startDate (fallback to visible text).
    """
    base = "https://www.sofistadium.com"
    robots = Robots(base)
    if not robots.load():
        if debug: print("[SOFI] robots unreachable")
        return []
    path = "/events"
    if not robots.can(path):
        if debug: print("[SOFI] disallowed by robots")
        return []

    html = polite_get(urljoin(base, path), robots.delay, debug)
    if not html:
        return []

    soup = BeautifulSoup(html, "lxml")
    # Cards per your snapshot
    cards = soup.select("#list.eventList__wrapper .eventItem, .eventList__wrapper .eventItem")
    if debug: print(f"[SOFI] list cards: {len(cards)}")

    out = []
    # Respect politeness: small delay between detail fetches if robots sets one
    per_req_delay = robots.delay or 1

    for i, card in enumerate(cards):
        title_el = card.select_one(".info h3.title, h3.title")
        title = title_el.get_text(strip=True) if title_el else None
        link_el = card.select_one("a[href]")
        if not link_el:
            if debug and i < 2: print("  [SOFI] no link for card")
            continue

        detail_url = urljoin(base, link_el["href"])

        # robots check for detail URL path
        detail_path = urlparse(detail_url).path or "/"
        if not robots.can(detail_path):
            if debug and i < 2: print(f"  [SOFI] robots disallow detail {detail_path}")
            continue

        # fetch detail
        detail_html = polite_get(detail_url, per_req_delay, debug)
        if not detail_html:
            continue

        start_iso, title_override = extract_event_from_detail(detail_html, base)
        final_title = (title_override or title or "").strip() or None

        if debug and i < 3:
            print(f"  [SOFI#{i}] detail -> start={start_iso} title={final_title!r} url={detail_url}")

        out.append({
            "venue": "SoFi Stadium",
            "title": final_title,
            "start_datetime_local": start_iso,
            "url": detail_url,
            "source": urljoin(base, path),
        })

    return out


# ---------------- KIA FORUM (via Ticketmaster Official API) ----------------
def scrape_kia_all(debug=False):
    """
    Kia Forum via Ticketmaster Discovery API
    """
    import os
    
    api_key = os.getenv("TICKETMASTER_API_KEY")
    if not api_key:
        if debug: print("[KIA] No TICKETMASTER_API_KEY env var")
        return []
    
    # API endpoint
    url = "https://app.ticketmaster.com/discovery/v2/events.json"
    params = {
        "venueId": "KovZpZAEkn6A",  # Kia Forum
        "apikey": api_key,
        "size": 200,
        "sort": "date,asc",
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code != 200:
            if debug: print(f"[KIA API] HTTP {response.status_code}")
            return []
        
        data = response.json()
    except Exception as e:
        if debug: print(f"[KIA API] Error: {e}")
        return []
    
    events = data.get("_embedded", {}).get("events", [])
    if debug: print(f"[KIA API] Found {len(events)} events")
    
    # Deduplicate by (date, time) - keep the one with better title
    seen = {}
    for event in events:
        title = event.get("name", "").strip()
        start_data = event.get("dates", {}).get("start", {})
        datetime_str = start_data.get("dateTime")
        event_url = event.get("url")
        
        if not title or not datetime_str:
            continue
        
        dt = to_la(datetime_str)
        if not dt:
            continue
        
        # Use date+time as key for deduplication
        key = dt.isoformat()
        
        # Prefer longer, more descriptive titles
        if key not in seen or len(title) > len(seen[key]["title"]):
            seen[key] = {
                "venue": "Kia Forum",
                "title": title,
                "start_datetime_local": dt.isoformat(),
                "url": event_url or "https://www.ticketmaster.com/kia-forum-tickets-inglewood/venue/73750",
                "source": "Ticketmaster Discovery API",
            }
    
    out = list(seen.values())
    
    if debug:
        print(f"[KIA API] After dedup: {len(out)} unique events")
        for i, ev in enumerate(out[:5]):
            print(f"  [KIA API] {ev['title']} @ {ev['start_datetime_local']}")
    
    return out

# ---------------- main ----------------
def main():
    ap = argparse.ArgumentParser(description="Inglewood venues: print today's events AND all events (LA time).")
    ap.add_argument("--date", help="YYYY-MM-DD used for 'today' filter (America/Los_Angeles). Default: actual today.", default=None)
    ap.add_argument("--pretty", action="store_true")
    ap.add_argument("--debug", action="store_true")
    ap.add_argument("--venue", choices=["intuit","sofi","kia","all"], default="all")
    args = ap.parse_args()

    target_date = la_today(args.date)
    if args.debug: print(f"[INFO] target_date={target_date}")

    all_events = []
    if args.venue in ("intuit","all"):
        all_events.extend(scrape_intuit_all(debug=args.debug))
    if args.venue in ("sofi","all"):
        all_events.extend(scrape_sofi_all(debug=args.debug))
    if args.venue in ("kia","all"):
        all_events.extend(scrape_kia_all(debug=args.debug))

    # de-dup ALL by (venue, title, date)
    seen = set()
    dedup_all = []
    for ev in all_events:
        k = (ev.get("venue"), ev.get("title"), (ev.get("start_datetime_local") or "")[:10])
        if k in seen: continue
        seen.add(k); dedup_all.append(ev)

    # filter TODAY
    today_events = []
    for ev in dedup_all:
        s = ev.get("start_datetime_local")
        if not s: continue
        try:
            d = dtparse.parse(s)
            d = d.astimezone(LA_TZ) if d.tzinfo else LA_TZ.localize(d)
            if d.date() == target_date:
                today_events.append(ev)
        except Exception:
            pass

    out = {"today": today_events, "all": dedup_all}
    data = collect_events(venue=args.venue, debug=args.debug)
    print(json.dumps(data, indent=2 if args.pretty else None, ensure_ascii=False))

def collect_events(venue="all", debug=False):
    # reuse your existing logic verbatim
    target_date = la_today(None)

    all_events = []
    if venue in ("intuit","all"):
        all_events.extend(scrape_intuit_all(debug=debug))
    if venue in ("sofi","all"):
        all_events.extend(scrape_sofi_all(debug=debug))
    if venue in ("kia","all"):
        all_events.extend(scrape_kia_all(debug=debug))

    # de-dup
    seen = set()
    dedup_all = []
    for ev in all_events:
        k = (ev.get("venue"), ev.get("title"), (ev.get("start_datetime_local") or "")[:10])
        if k in seen: 
            continue
        seen.add(k)
        dedup_all.append(ev)

    # filter TODAY
    today_events = []
    for ev in dedup_all:
        s = ev.get("start_datetime_local")
        if not s: 
            continue
        try:
            d = dtparse.parse(s)
            d = d.astimezone(LA_TZ) if d.tzinfo else LA_TZ.localize(d)
            if d.date() == target_date:
                today_events.append(ev)
        except Exception:
            pass

    return {"today": today_events, "all": dedup_all}

if __name__ == "__main__":
    main()
