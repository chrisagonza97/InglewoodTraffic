# InglewoodCrawler – Local + Dockerized Ingest Pipeline

This project scrapes event data for Inglewood venues and ingests it into a PostgreSQL database on a daily schedule.  
You can develop, test, and deploy it entirely in Docker.

---

## 🗂️ Directory Structure

```
InglewoodCrawler/
├─ ingest_pg.py
├─ inglewood_events_cli.py
├─ check_db.py
├─ Dockerfile
├─ docker-compose.yml
├─ requirements.txt
├─ .env
├─ Makefile
└─ docker/
   ├─ initdb/
   │  ├─ 00_init.sh
   │  └─ 01_schema.sql
   ├─ crontab
   └─ (optional: wait-for.sh)
```

---

## ⚙️ 1. Setup (first time)

### 0. Activate venv `.env`
```bash
.\venv\Scripts\Activate.ps1    
```

### A. Create `.env`
```bash
POSTGRES_PASSWORD=admin
ING_USER_PASSWORD=adminadmin
```

### B. Build containers
```bash
docker compose build
```

### C. Start PostgreSQL + Scheduler + API (runs init scripts automatically)
```bash
docker compose up -d db scheduler api
docker logs -f igw_db
```
Wait until you see:
```
database system is ready to accept connections
```

---

## 🚀 2. One-Shot Ingest Run

Populate the database by running:
```bash
docker compose run --rm --entrypoint bash ingest -lc "python -u ingest_pg.py"
```

You should see output like:
```
{'ingested': 62}
```

---

## 🔍 3. Verify Database Contents

Check row count and sample rows:
```bash
docker exec -it igw_db psql -U postgres -d inglewood -c "SELECT COUNT(*) FROM events;"
docker exec -it igw_db psql -U postgres -d inglewood -c "SELECT venue,title,start_at_la,start_date FROM events ORDER BY last_seen_at DESC LIMIT 10;"
```

Run a quick sanity check script:
```bash
docker compose run --rm --entrypoint bash ingest -lc "python check_db.py"
```

---

## ♻️ 4. Reset or Reinitialize

If the init scripts didn’t run or you changed passwords:
```bash
make down
make up-dev
```
**Warning:** This deletes all DB data.

---

## 🕒 5. Daily Scheduler (Automatic Ingest)

1. The cron schedule is defined in `docker/crontab`:
   ```bash
   SHELL=/bin/bash
   PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
   TZ=America/Los_Angeles
   @reboot cd /app && python ingest_pg.py >> /var/log/ingest.log 2>&1
   0 4 * * * cd /app && python ingest_pg.py >> /var/log/ingest.log 2>&1
   ```

   - `@reboot` ensures ingestion runs automatically whenever the container restarts.
   - `0 4 * * *` runs ingestion every day at **4:00 AM LA time**.

2. Confirm logs:
   ```bash
   docker logs -f igw_scheduler
   ```

3. (Optional) Inspect recent ingest logs inside container:
   ```bash
   docker exec -it igw_scheduler bash -lc "tail -n 50 /var/log/ingest.log"
   ```

---

## 🧹 6. Clean Shutdown

```bash
make down
```

---

## 🧪 7. Makefile Commands

| Task | Command | Description |
|------|----------|-------------|
| Start dev stack | `make up-dev` | Spins up DB, API, and scheduler using `.env.dev` |
| Start prod stack | `make up-prod` | Spins up all services (db + api + scheduler + proxy) |
| Stop everything | `make down` | Stops and removes containers |
| Show logs | `make logs` | Streams logs for all services |
| Rebuild images | `make rebuild` | Rebuilds all Docker images |
| Check health | `make check` | Calls FastAPI health endpoint |
| DB shell | `make shell-db` | Opens psql shell inside DB |
| API shell | `make shell-api` | Opens bash inside API container |

---

## ✅ 8. Expected Behavior

- First run → creates DB, schema, and user.  
- Every ingest → upserts new/updated events (`ON CONFLICT (venue,title,start_date)`).  
- Running multiple times does **not** duplicate rows.  
- Scheduler automatically runs at 4 AM LA time and once at startup.

---

## 🌐 9. API Endpoints

| Endpoint | Description |
|-----------|-------------|
| `/healthz` | Health + DB status summary |
| `/events/today` | Returns events for the current day |
| `/events/upcoming?limit=50` | Returns upcoming events |
| `/events/past` | Returns past events |

---

## 💡 10. Development Tips

- Use `make down` and `make up-dev` to restart cleanly.  
- The `.env.dev` and `.env.prod` files separate credentials for local and production use.  
- You can run the Vite frontend separately with:  
  ```bash
  cd frontend
  npm run dev
  ```

---

© 2025 InglewoodCrawler – Event ingestion and visualization stack for Inglewood venues.
