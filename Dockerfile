# syntax=docker/dockerfile:1
FROM python:3.11-slim

# ---- Environment ----
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=America/Los_Angeles

# ---- OS deps (minimal) ----
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ---- Supercronic for scheduler ----
ADD https://github.com/aptible/supercronic/releases/download/v0.2.29/supercronic-linux-amd64 /usr/local/bin/supercronic
RUN chmod +x /usr/local/bin/supercronic && mkdir -p /var/log

# ---- Python deps ----
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- App code ----
COPY . .

# ---- Default (overridden by docker-compose for api/scheduler) ----
CMD ["python", "ingest_pg.py"]
