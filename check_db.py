#!/usr/bin/env python3
import psycopg2
import os

PG_DSN = os.getenv("PG_DSN", "postgresql://ing_user:adminadmin@127.0.0.1:5432/inglewood")

def check_db():
    try:
        conn = psycopg2.connect(PG_DSN)
        cur = conn.cursor()
        cur.execute("""
            SELECT venue, title, start_at_la, start_date
            FROM public.events
            ORDER BY start_at_la ASC
            LIMIT 1;
        """)
        row = cur.fetchone()
        if row:
            venue, title, start_at_la, start_date = row
            print(f"--- Database Connection Successful ---")
            print(f"Venue: {venue}")
            print(f"Event: {title}")
            print(f"Start (LA time): {start_at_la}")
            print(f"Start Date: {start_date}")
        else:
            print("Connected to DB, but no events found.")
    except Exception as e:
        print(f"*** ERROR: {type(e).__name__} ***")
        print(str(e))
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_db()
