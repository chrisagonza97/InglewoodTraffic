import os
from datetime import datetime, timedelta
from pathlib import Path

LOCK_FILE = Path("/tmp/last_scrape.lock")
MIN_INTERVAL_HOURS = 1  # Don't scrape more than once per hour

def can_scrape():
    if not LOCK_FILE.exists():
        return True
    
    last_scrape = datetime.fromtimestamp(LOCK_FILE.stat().st_mtime)
    if datetime.now() - last_scrape > timedelta(hours=MIN_INTERVAL_HOURS):
        return True
    
    return False

def mark_scraped():
    LOCK_FILE.touch()