# 🔧 ClipForge Startup Troubleshooting Guide

If you encounter startup failures, use this guide to diagnose and fix issues.

---

## ✅ Issues Fixed & Resolved

### 1. **Missing .env File**

**Error:**
```
env file E:\PROJECT\clipforge\clipforge\.env not found
```

**Cause:** `.env` is excluded from git (.gitignore)

**Solution:**
```bash
cp .env.example .env
```

**Status:** ✅ **FIXED** - `.env` now created automatically

---

### 2. **Docker Compose Version Warning**

**Warning:**
```
the attribute `version` is obsolete, it will be ignored
```

**Cause:** Docker Compose deprecated the `version` field in Compose files

**Solution:** Remove `version: "3.9"` from docker-compose.yml

**Status:** ✅ **FIXED** - Version removed from both compose files

---

### 3. **MinIO Image Pull Failed**

**Error:**
```
pull access denied for minio/minio, repository does not exist or may require 'docker login'
```

**Cause:** `minio/minio:latest` not accessible from Docker Hub in some regions

**Solution:** Changed to `quay.io/minio/minio:latest`

**Steps Taken:**
```bash
# Updated docker-compose.yml:
image: quay.io/minio/minio:latest  # (was: minio/minio:latest)

# Pre-pulled the image:
docker pull quay.io/minio/minio:latest
```

**Status:** ✅ **FIXED** - MinIO now uses quay.io registry

---

## 🚀 Current Startup Status

All services verified working:

```
✅ postgres:16-alpine       — Running & healthy
✅ redis:7-alpine           — Running & healthy  
✅ quay.io/minio/minio      — Running & healthy
✅ clipforge-api            — Running & ready
✅ clipforge-web            — Running & ready
✅ clipforge-worker         — Running & listening on 3 queues
```

---

## 📋 Quick Verification Checklist

After `docker-compose up -d`, run these checks:

```bash
# 1. Check all containers running
docker-compose ps
# Expected: 6 containers with status "Up"

# 2. Test API
curl http://localhost:8000/docs
# Expected: HTTP 200 with Swagger UI

# 3. Test Web
curl http://localhost:3000
# Expected: HTTP 200 with HTML

# 4. Test MinIO
curl http://localhost:9001
# Expected: HTTP 200 with console

# 5. Test Database
docker-compose exec -T postgres psql -U clipforge -d clipforge -c "\dt"
# Expected: 7 tables listed

# 6. Test Redis
docker-compose exec -T redis redis-cli ping
# Expected: PONG

# 7. Check logs
docker-compose logs -f api
# Expected: "Application startup complete"
```

---

## 🆘 If Startup Still Fails

### Step 1: Check .env exists

```bash
ls -la .env
# If missing:
cp .env.example .env
```

### Step 2: Check Docker images

```bash
docker images | grep -E "postgres|redis|minio|clipforge"

# If missing, build them:
docker-compose build
```

### Step 3: Check Docker daemon

```bash
docker ps
# If error: Docker daemon not running
```

### Step 4: View detailed logs

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs -f api
docker-compose logs -f web
docker-compose logs -f worker
docker-compose logs -f postgres
```

### Step 5: Clean and restart

```bash
# Stop all
docker-compose down

# Remove images
docker-compose down -v

# Rebuild and start
docker-compose build
docker-compose up -d

# Check logs
docker-compose logs -f
```

---

## 🔍 Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Port 3000 already in use | Another service on port | Change port in docker-compose.yml |
| Port 8000 already in use | Another service on port | Change port in docker-compose.yml |
| Database won't initialize | init.sql not found | Check `./infra/init.sql` exists |
| Worker exits immediately | Missing Python deps | Check worker Dockerfile, rebuild |
| Web won't load | API not responding | Check API logs: `docker-compose logs api` |
| MinIO won't start | Image not available | Pre-pull: `docker pull quay.io/minio/minio:latest` |
| Redis connection failed | .env Redis URL wrong | Check `.env`: `REDIS_URL=redis://redis:6379/0` |
| Postgres connection failed | .env Postgres URL wrong | Check `.env` database variables |

---

## 📝 Environment Variables (.env)

Verify these are set:

```bash
# Core
ENV=development
SECRET_KEY=change-me

# Postgres
POSTGRES_USER=clipforge
POSTGRES_PASSWORD=clipforge
POSTGRES_DB=clipforge

# Redis
REDIS_URL=redis://redis:6379/0

# S3 (MinIO)
S3_ENDPOINT_URL=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin

# Web
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# LLM (optional in dev)
LLM_API_KEY=  # Leave empty for dev

# Whisper (optional in dev)
WHISPER_MODEL_SIZE=small
WHISPER_DEVICE=cpu
```

---

## 🧹 Clean Up & Reset

If you need a fresh start:

```bash
# Stop and remove everything
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Remove .env
rm .env

# Start fresh
cp .env.example .env
docker-compose build
docker-compose up -d
```

---

## 📊 System Health Check Script

Create `health-check.sh`:

```bash
#!/bin/bash

echo "🔍 ClipForge Health Check"
echo ""

# Check containers
echo "1. Checking containers..."
docker-compose ps

echo ""
echo "2. Testing API..."
curl -s http://localhost:8000/docs | head -c 50 && echo " ✅"

echo ""
echo "3. Testing Web..."
curl -s http://localhost:3000 | head -c 50 && echo " ✅"

echo ""
echo "4. Testing MinIO..."
curl -s http://localhost:9001 | head -c 50 && echo " ✅"

echo ""
echo "5. Testing Postgres..."
docker-compose exec -T postgres pg_isready -U clipforge

echo ""
echo "6. Testing Redis..."
docker-compose exec -T redis redis-cli ping

echo ""
echo "✅ Health check complete!"
```

Run it:
```bash
chmod +x health-check.sh
./health-check.sh
```

---

## 📞 Getting Help

| Issue | Documentation |
|-------|----------------|
| Can't access API | [VERIFICATION_REPORT.md](VERIFICATION_REPORT.md) |
| Docker errors | [DOCKER_OPTIMIZATION.md](DOCKER_OPTIMIZATION.md) |
| CI/CD pipeline | [GITHUB_DEPLOYMENT.md](GITHUB_DEPLOYMENT.md) |
| Architecture | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Commands | [COMMANDS.md](COMMANDS.md) |

---

## ✅ Final Status

**All known startup issues have been:**
- ✅ Identified
- ✅ Fixed
- ✅ Tested
- ✅ Documented

**Current Status:** 🟢 **READY FOR DEPLOYMENT**

If issues persist, check:
1. `.env` file exists and is readable
2. Docker daemon is running
3. Port 3000, 8000, 5432, 6379, 9000, 9001 are available
4. Images built with `docker-compose build`
5. Run `docker-compose logs` to see detailed error messages

