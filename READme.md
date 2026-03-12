# Inglewood Events Tracker

A real-time event aggregation and traffic advisory system for Inglewood's three major venues: **Kia Forum**, **SoFi Stadium**, and **Intuit Dome**. Helps locals and commuters avoid traffic congestion by tracking upcoming events and providing traffic alerts.

---

## 🎯 Project Overview

Inglewood hosts some of LA's biggest entertainment venues, leading to significant traffic during events. This application:
- **Scrapes** event data from venue websites daily
- **Displays** upcoming events in an intuitive web interface
- **Provides** traffic advisories for peak event times
- **Maps** key traffic corridors (Century Blvd & Prairie Ave)

**Live Example:** Access via `http://YOUR_DROPLET_IP` or domain after deployment.

---

## 🛠️ Tech Stack

### **Backend**
- **Python 3.11** - Core scraping and API logic
- **FastAPI** - RESTful API with async support
- **PostgreSQL 16** - Event data storage with timezone support
- **BeautifulSoup4 + Requests** - Web scraping with robots.txt compliance
- **Psycopg2** - PostgreSQL adapter
- **Supercronic** - Cron-based job scheduler for daily ingestion

### **Frontend**
- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **TanStack Query** - Server state management and caching
- **Leaflet** - Interactive traffic maps
- **Nginx** - Production web server (in Docker)

### **Infrastructure**
- **Docker & Docker Compose** - Containerized deployment
- **Caddy 2** - Reverse proxy with automatic HTTPS/SSL
- **DigitalOcean Droplet** - VPS hosting (Ubuntu 24.04)

### **Development**
- **Git/GitHub** - Version control
- **Make** - Task automation
- **PowerShell/Bash** - Scripting and automation

---

## 📁 Directory Structure

```
InglewoodTraffic/
├─ api.py                          # FastAPI application
├─ ingest_pg.py                    # Database ingestion script
├─ inglewood_events_cli.py         # Venue scraping logic
├─ check_db.py                     # Database verification utility
├─ Dockerfile                      # Backend container image
├─ docker-compose.yml              # Development services
├─ docker-compose.prod.yml         # Production services (not in git)
├─ requirements.txt                # Python dependencies
├─ .env.dev                        # Development environment vars
├─ .env.prod                       # Production secrets (not in git)
├─ Makefile                        # Task automation
├─ README.md                       # This file
│
├─ docker/
│  ├─ initdb/
│  │  ├─ 00_init.sh               # Database initialization
│  │  └─ 01_schema.sql            # Database schema
│  ├─ crontab                      # Scheduled job configuration
│  └─ Caddyfile                    # Reverse proxy configuration
│
└─ ing-frontend/
   ├─ src/
   │  ├─ components/               # React components
   │  ├─ hooks/                    # React hooks (API calls)
   │  ├─ lib/                      # Utilities (API client)
   │  ├─ maps/                     # Map configuration
   │  └─ utils/                    # Helper functions
   ├─ public/                      # Static assets
   ├─ package.json                 # Node dependencies
   ├─ vite.config.js               # Vite configuration
   ├─ Dockerfile                   # Frontend container image
   ├─ nginx.conf                   # Production web server config
   ├─ .env                         # Development API URL
   └─ .env.production              # Production API URL (not in git)
```

---

## ⚙️ Setup & Development

### **Prerequisites**
- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Node.js 20+ (for local frontend development)
- Python 3.11+ (for local backend development)
- Git

### **1. Clone Repository**
```bash
git clone https://github.com/chrisagonza97/InglewoodTraffic.git
cd InglewoodTraffic
```

### **2. Start Development Environment**

#### **Backend (Docker):**
```bash
# Start database, API, and scheduler
make up-dev

# Wait for database to be ready
docker logs -f igw_db
# Look for: "database system is ready to accept connections"
```

#### **Frontend (Local - Hot Reload):**
```bash
cd ing-frontend
npm install
npm run dev

# Frontend runs on http://localhost:5173
# API runs on http://localhost:8000
```

### **3. Initial Data Ingestion**
```bash
# Populate database with events
docker exec -it igw_scheduler python -u ingest_pg.py

# Verify data
docker exec -it igw_db psql -U postgres -d inglewood -c "SELECT COUNT(*) FROM events;"
```

---

## 🚀 Deployment (Production)

### **Prerequisites**
- DigitalOcean account (or any VPS provider)
- Domain name (optional but recommended)

### **1. Create Droplet**
- **OS:** Ubuntu 24.04 LTS
- **Size:** Basic $6/month (1GB RAM, 25GB SSD)
- **Region:** Los Angeles or San Francisco
- **Authentication:** SSH key or password

### **2. SSH Into Droplet**
```bash
ssh root@YOUR_DROPLET_IP
```

### **3. Install Docker**
```bash
apt update && apt upgrade -y
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
docker --version
```

### **4. Clone Repository**
```bash
git clone https://github.com/chrisagonza97/InglewoodTraffic.git
cd InglewoodTraffic
```

### **5. Create Production Configuration**

#### **A. Generate Secure Passwords**
```bash
openssl rand -base64 32  # POSTGRES_PASSWORD
openssl rand -base64 32  # ING_USER_PASSWORD
openssl rand -base64 32  # API_KEY
```

#### **B. Create `.env.prod`**
```bash
nano .env.prod
```

Paste (replace with your generated passwords):
```bash
POSTGRES_PASSWORD=YOUR_POSTGRES_PASSWORD
ING_USER_PASSWORD=YOUR_ING_USER_PASSWORD
PG_DSN=postgresql://ing_user:YOUR_ING_USER_PASSWORD@db:5432/inglewood
ALLOWED_ORIGINS=http://YOUR_DROPLET_IP
API_KEY=YOUR_API_KEY
RETENTION_DAYS=0
```

#### **C. Create `docker-compose.prod.yml`**
```bash
nano docker-compose.prod.yml
```

Copy the production compose configuration (see repository for template).

#### **D. Create `ing-frontend/.env.production`**
```bash
nano ing-frontend/.env.production
```

Paste:
```
VITE_API_URL=/api
```

### **6. Deploy**
```bash
# Start all services
make up-prod

# Verify containers are running
docker ps

# Run initial data ingestion
docker exec -it igw_scheduler python -u ingest_pg.py
```

### **7. Access Your Site**
```
http://YOUR_DROPLET_IP
```

### **8. (Optional) Add Domain + SSL**

#### **A. Point Domain to Droplet**
Add DNS records:
- **A record:** `@` → `YOUR_DROPLET_IP`
- **A record:** `www` → `YOUR_DROPLET_IP`

#### **B. Update Caddyfile**
```bash
nano docker/Caddyfile
```

Change `:80` to `yourdomain.com`:
```
yourdomain.com {
    # Your existing routes
}
```

#### **C. Update Frontend ALLOWED_ORIGINS**
```bash
nano .env.prod
```

Change:
```
ALLOWED_ORIGINS=https://yourdomain.com
```

#### **D. Restart**
```bash
make down
make up-prod
```

Caddy automatically provisions SSL certificate from Let's Encrypt! 🔒

Access: `https://yourdomain.com`

---

## 🧪 Makefile Commands

| Command | Description |
|---------|-------------|
| `make up-dev` | Start development (DB, API, scheduler only) |
| `make up-prod-local` | Test production build locally (all services) |
| `make up-prod` | Deploy production (use on droplet) |
| `make down` | Stop all services |
| `make logs` | View container logs |
| `make rebuild` | Rebuild Docker images |
| `make ingest` | Manually run data ingestion |
| `make reset-db` | Clear all events from database |
| `make check` | Test API health (dev) |
| `make shell-db` | Open PostgreSQL shell |
| `make shell-api` | Open API container shell |
| `make shell-scheduler` | Open scheduler container shell |

---

## 🔍 Verification & Debugging

### **Check Services**
```bash
# All containers running
docker ps

# API health
curl http://localhost/healthz

# Get today's events
curl http://localhost/events/today

# Get upcoming events
curl http://localhost/events/upcoming?limit=10
```

### **Database Inspection**
```bash
# Count events
docker exec -it igw_db psql -U postgres -d inglewood -c "SELECT COUNT(*) FROM events;"

# View recent events
docker exec -it igw_db psql -U postgres -d inglewood -c "
SELECT venue, title, start_date, start_at_la 
FROM events 
ORDER BY start_at_la 
LIMIT 10;
"

# Check by venue
docker exec -it igw_db psql -U postgres -d inglewood -c "
SELECT venue, COUNT(*) 
FROM events 
GROUP BY venue;
"
```

### **View Logs**
```bash
# API logs
docker logs igw_api

# Scheduler logs (cron)
docker logs igw_scheduler

# Database logs
docker logs igw_db

# Caddy proxy logs
docker logs igw_proxy

# Ingestion history
docker exec -it igw_scheduler tail -50 /var/log/ingest.log
```

---

## 🕒 Automated Ingestion

Events are automatically scraped daily at **4:00 AM LA time** via cron job.

**Configuration:** `docker/crontab`
```bash
TZ=America/Los_Angeles
0 4 * * * cd /app && python -u ingest_pg.py >> /var/log/ingest.log 2>&1
```

**Features:**
- ✅ Scrapes all three venues (Kia Forum, SoFi, Intuit Dome)
- ✅ Updates existing events (no duplicates)
- ✅ Removes past events automatically
- ✅ Respects robots.txt and rate limits
- ✅ Logs all operations

---

## 🌐 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/healthz` | GET | Health check + DB status |
| `/events/today` | GET | Events happening today (LA timezone) |
| `/events/upcoming` | GET | Future events (limit parameter supported) |
| `/events/week` | GET | Events for current/next week (week parameter: 0 or 1) |

**Example:**
```bash
curl http://localhost/events/upcoming?limit=20
```

---

## 🛡️ Security Features

- ✅ **Read-only database user** for API (no write access)
- ✅ **Rate limiting** on API endpoints (60 req/min per IP)
- ✅ **CORS protection** (only allowed origins)
- ✅ **No exposed database ports** in production
- ✅ **Resource limits** on containers (CPU/memory caps)
- ✅ **Scraping cooldown** (max 1 ingestion per hour)
- ✅ **Automatic HTTPS** via Caddy + Let's Encrypt
- ✅ **Container hardening** (read-only filesystems, dropped capabilities)

---

## 💰 Cost Breakdown (DigitalOcean)

| Item | Cost |
|------|------|
| **Droplet** (1GB RAM, 25GB SSD) | $6/month |
| **Bandwidth** (1TB included) | $0 |
| **Domain** (optional) | ~$10/year |
| **SSL Certificate** | Free (Let's Encrypt) |
| **Total** | **~$6/month** |

**Note:** Hourly billing = ~$0.009/hour, so testing costs pennies!

---

## 🐛 Troubleshooting

### **Events not showing**
```bash
# Check if data exists
docker exec -it igw_db psql -U postgres -d inglewood -c "SELECT COUNT(*) FROM events;"

# Run manual ingestion
docker exec -it igw_scheduler rm /tmp/last_scrape.lock
docker exec -it igw_scheduler python -u ingest_pg.py
```

### **API not accessible**
```bash
# Check API is running
docker ps | grep api

# Check API logs
docker logs igw_api

# Test directly
docker exec igw_api curl http://localhost:8000/healthz
```

### **Frontend shows blank/errors**
```bash
# Check frontend container
docker logs igw_frontend

# Check Caddy proxy
docker logs igw_proxy

# Hard refresh browser
# Windows: Ctrl + Shift + R
# Mac: Cmd + Shift + R
```

### **"Failed to construct URL" error**
The frontend build might be cached. Rebuild:
```bash
make down
docker rmi inglewoodcrawler-frontend
docker compose --env-file .env.dev --profile prod -f docker-compose.yml -f docker-compose.prod.yml build --no-cache frontend
make up-prod-local
```

---

## 📊 Data Sources

| Venue | Source | Update Frequency |
|-------|--------|------------------|
| **Kia Forum** | Ticketmaster API | Daily at 4 AM |
| **SoFi Stadium** | sofistadium.com | Daily at 4 AM |
| **Intuit Dome** | intuitdome.com | Daily at 4 AM |

All scrapers:
- ✅ Respect robots.txt
- ✅ Use polite delays (1-10 seconds)
- ✅ Include proper User-Agent
- ✅ Handle errors gracefully

---

## 🤝 Contributing

This is a personal project, but suggestions and bug reports are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally with `make up-prod-local`
5. Submit a pull request

---

## 📝 License

MIT License - feel free to use and modify for your own projects.

---

## 🙏 Acknowledgments

- **OpenStreetMap** - Traffic map tiles
- **Leaflet** - Map rendering library
- **Ticketmaster** - Kia Forum event data
- Event data from venue websites (SoFi Stadium, Intuit Dome)

---

## 📧 Contact

For questions or issues:
- Open a GitHub issue
- Email: [your-email@example.com]

---

**Built with ❤️ to help Inglewood commuters avoid traffic!**

---

© 2025 Inglewood Events Tracker – Real-time event aggregation for traffic awareness.
