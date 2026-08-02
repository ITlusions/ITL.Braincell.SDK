# Deployment Guide

Complete guide to deploying BrainCell in production.

## Prerequisites

- Python 3.12+
- PostgreSQL 14+
- Weaviate v4
- Redis (optional, for caching)
- Docker & Docker Compose (recommended)

---

## Docker Compose (Recommended)

### Quick Start

Create `docker-compose.yml`:

```yaml
version: '3.9'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: braincell
      POSTGRES_PASSWORD: ${DB_PASSWORD:-password}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  weaviate:
    image: semitechnologies/weaviate:latest
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      PERSISTENCE_DATA_PATH: /var/lib/weaviate
    ports:
      - "8080:8080"
    volumes:
      - weaviate_data:/var/lib/weaviate
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8080/v1/.well-known/ready || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  weaviate_data:
  redis_data:
```

Start services:

```bash
docker compose up -d

# Check health
docker compose ps
```

---

## Environment Configuration

### Required Variables

```bash
# Database
export BRAINCELL_DATABASE_URL="postgresql+asyncpg://postgres:password@localhost/braincell"

# Weaviate
export BRAINCELL_WEAVIATE_URL="http://localhost:8080"

# Redis (optional)
export BRAINCELL_REDIS_URL="redis://localhost:6379"
```

### Optional Variables

```bash
# Logging
export BRAINCELL_LOG_LEVEL="INFO"

# API
export BRAINCELL_API_HOST="0.0.0.0"
export BRAINCELL_API_PORT="9504"

# Plugin Configuration
export BRAINCELL_SECURITY_API_KEY="your-api-key"
export BRAINCELL_SECURITY_THREAT_ALERT_THRESHOLD="7"
```

### Load from .env File

Create `.env`:

```bash
BRAINCELL_DATABASE_URL=postgresql+asyncpg://postgres:password@localhost/braincell
BRAINCELL_WEAVIATE_URL=http://localhost:8080
BRAINCELL_REDIS_URL=redis://localhost:6379
BRAINCELL_LOG_LEVEL=INFO
```

Load it:

```bash
set -a
source .env
set +a
```

---

## Database Migrations

### Run Migrations

```bash
# Using Alembic directly
python -m alembic upgrade head

# Check current revision
python -m alembic current

# Check history
python -m alembic history
```

### Migration Strategy

**Development:**
```bash
# Auto-generate migration
alembic revision --autogenerate -m "Add new column"

# Apply
alembic upgrade head
```

**Production:**
```bash
# Review migrations first
alembic history

# Apply only after verification
alembic upgrade head

# Verify
alembic current
```

### Handling Migration Errors

**Table already exists:**
```bash
alembic stamp head  # Mark as applied without re-creating
```

**Downgrade**:
```bash
alembic downgrade -1  # Go back one migration
alembic downgrade base  # Go back to initial state
```

---

## Running the API

### Development

```bash
pip install -e .

uvicorn main:app --reload --host 0.0.0.0 --port 9504
```

### Production

```bash
uvicorn main:app \
  --host 0.0.0.0 \
  --port 9504 \
  --workers 4 \
  --access-log \
  --log-config logging_config.yaml
```

### Docker Container

Create `Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9504"]
```

Build and run:

```bash
docker build -t braincell-api:latest .

docker run \
  --env-file .env \
  --network braincell_default \
  -p 9504:9504 \
  braincell-api:latest
```

---

## Verify Installation

### Health Check

```bash
curl http://localhost:9504/health
```

### List Plugins

```bash
curl http://localhost:9504/api/plugins | jq
```

### Get Metrics

```bash
curl http://localhost:9504/api/plugins/security/metrics | jq
```

---

## Production Checklist

- ✅ PostgreSQL running and initialized
- ✅ Weaviate running and reachable
- ✅ Redis running (if using caching)
- ✅ Environment variables set
- ✅ Database migrations applied
- ✅ SSL/TLS certificates installed (for HTTPS)
- ✅ Secrets stored in secure vault (not in code)
- ✅ Logging configured and monitored
- ✅ Backups scheduled for database
- ✅ Health checks configured
- ✅ Rate limiting configured (if needed)
- ✅ CORS configured for allowed origins

---

## Scaling Considerations

### Horizontal Scaling

```yaml
services:
  api-1:
    image: braincell-api:latest
    environment:
      - INSTANCE_ID=1
    depends_on:
      - postgres
      - weaviate

  api-2:
    image: braincell-api:latest
    environment:
      - INSTANCE_ID=2
    depends_on:
      - postgres
      - weaviate

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - api-1
      - api-2
```

### Database Optimization

```python
# Increase connection pool
engine = create_async_engine(
    database_url,
    pool_size=50,  # More connections
    max_overflow=10,
    pool_pre_ping=True,
    echo=False,
)
```

---

## Monitoring

### Logging

Enable debug logging:
```bash
export BRAINCELL_LOG_LEVEL=DEBUG
```

Structured logging output:
```json
{
  "timestamp": "2026-08-03T14:30:00Z",
  "level": "INFO",
  "message": "Plugin security initialized",
  "plugin": "security",
  "duration_ms": 125
}
```

### Health Monitoring

```bash
# API health
curl http://localhost:9504/health

# Database connection
curl http://localhost:9504/db/health

# Plugin metrics
curl http://localhost:9504/api/plugins/security/metrics
```

---

## Backup & Restore

### Backup Database

```bash
pg_dump -U postgres braincell > backup.sql

# With docker
docker exec braincell-postgres pg_dump -U postgres braincell > backup.sql
```

### Restore Database

```bash
psql -U postgres braincell < backup.sql

# With docker
cat backup.sql | docker exec -i braincell-postgres psql -U postgres braincell
```

### Automated Backups

```bash
#!/bin/bash
BACKUP_DIR=/backups
DB_NAME=braincell

DATE=$(date +%Y%m%d_%H%M%S)
FILE=$BACKUP_DIR/backup_$DATE.sql

pg_dump -U postgres $DB_NAME > $FILE
gzip $FILE

# Clean up old backups (keep last 30 days)
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
```

---

## Troubleshooting

See [Troubleshooting Guide](06-TROUBLESHOOTING.md)

**Next:** [Troubleshooting](06-TROUBLESHOOTING.md)
