# ClipForge Quick Reference

## 🔗 Push to GitHub

```bash
cd clipforge
git remote add origin https://github.com/YOUR_USERNAME/clipforge.git
git branch -M main
git push -u origin main
```

Then watch the build at: `https://github.com/YOUR_USERNAME/clipforge/actions`

---

## 📦 View Built Images

After workflow completes:
1. Go to: `https://github.com/YOUR_USERNAME/clipforge`
2. Click **Packages** tab
3. Images available at:
   - `ghcr.io/your-org/clipforge/api:latest`
   - `ghcr.io/your-org/clipforge/worker:latest`
   - `ghcr.io/your-org/clipforge/web:latest`

---

## 🚀 Deploy Locally

```bash
# 1. Set variables
export REGISTRY_URL=ghcr.io/your-org/clipforge
export APP_VERSION=main

# 2. Login to GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# 3. Deploy
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# 4. Check status
docker-compose -f docker-compose.prod.yml ps
```

---

## 📊 Monitor Services

```bash
# View all containers
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f [service]

# Services: api, worker, web, postgres, redis, minio

# Check health
curl http://localhost:8000/docs     # API
curl http://localhost:3000          # Web
curl http://localhost:9001          # MinIO
```

---

## 🔧 Troubleshooting

### Check what's running
```bash
docker ps
docker logs [container-id]
```

### Rebuild (if changes made)
```bash
git add .
git commit -m "Fix: update API"
git push origin main
# Wait for GitHub Actions to complete, then pull new images
```

### Stop everything
```bash
docker-compose -f docker-compose.prod.yml down
```

### Remove all data (clean slate)
```bash
docker-compose -f docker-compose.prod.yml down -v
```

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `.github/workflows/docker-build.yml` | GitHub Actions CI/CD |
| `docker-compose.prod.yml` | Production deployment |
| `apps/api/Dockerfile` | API image |
| `apps/worker/Dockerfile` | Worker image |
| `apps/web/Dockerfile.prod` | Web image (production) |
| `build.sh` / `build.bat` | Manual build scripts |
| `GITHUB_DEPLOYMENT.md` | This deployment guide |

---

## 🌐 URLs (Local Dev)

| Service | URL |
|---------|-----|
| Web App | http://localhost:3000 |
| API Docs | http://localhost:8000/docs |
| MinIO Console | http://localhost:9001 |
| Postgres | localhost:5432 |
| Redis | localhost:6379 |

---

## 📝 Configure Production

Edit `.env` before deploying:

```bash
ENV=production
SECRET_KEY=your-secret-here
POSTGRES_PASSWORD=your-postgres-password
LLM_API_KEY=your-claude-api-key
S3_ACCESS_KEY=your-s3-key
S3_SECRET_KEY=your-s3-secret
NEXT_PUBLIC_API_BASE_URL=https://api.yoursite.com
```

---

## 🔄 Redeploy After Code Changes

```bash
# 1. Make changes locally
# 2. Commit and push
git add .
git commit -m "feat: add feature"
git push origin main

# 3. GitHub Actions builds automatically
# 4. Pull and redeploy
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d -f

# 5. Check status
docker-compose -f docker-compose.prod.yml logs -f
```

---

## 🐛 Debug Failed Workflow

1. Go to: `https://github.com/YOUR_USERNAME/clipforge/actions`
2. Click the failed workflow run
3. Expand the failed step to see error message
4. Common issues:
   - Branch name not `main` or `develop`
   - Missing Dockerfile (check path)
   - `.dockerignore` incorrectly excluding files

---

## 📚 More Info

- Full deployment guide: `GITHUB_DEPLOYMENT.md`
- Docker optimization details: `DOCKER_OPTIMIZATION.md`
- Registry setup: `REGISTRY_CICD_SETUP.md`
- Build Cloud: `DOCKER_BUILD_CLOUD.md`

---

**Need help?** Check the detailed guides above or visit: https://github.com/your-org/clipforge/issues

