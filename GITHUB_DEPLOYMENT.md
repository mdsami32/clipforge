# 🚀 ClipForge: GitHub Push & Automated Deployment Guide

Your code is now committed locally and ready to push to GitHub. Follow these steps to trigger CI/CD and deploy.

---

## Step 1: Create GitHub Repository

If you don't have a GitHub repository yet:

1. Go to [github.com/new](https://github.com/new)
2. **Repository name**: `clipforge` (or your preferred name)
3. **Description**: `Self-hosted alternative to Opus Clip with AI-powered vertical video editing`
4. **Visibility**: Public or Private (both work with GitHub Actions)
5. Click **Create repository**

---

## Step 2: Link Local Repository to GitHub

In your terminal/PowerShell:

```bash
cd clipforge

# Add GitHub remote
git remote add origin https://github.com/YOUR_USERNAME/clipforge.git

# Rename branch to main (if needed)
git branch -M main

# Push all commits
git push -u origin main
```

**Replace** `YOUR_USERNAME` with your actual GitHub username.

### Using SSH (Optional, More Secure)

If you have SSH keys set up:

```bash
git remote add origin git@github.com:YOUR_USERNAME/clipforge.git
git push -u origin main
```

---

## Step 3: Verify GitHub Actions Workflow

Once pushed, GitHub automatically detects and runs the workflow:

1. Go to your repository on GitHub
2. Click **Actions** tab
3. You should see **Build and Push Docker Images** running
4. Click the run to watch build progress

### What the Workflow Does:
- ✅ Detects changes to `apps/api/`, `apps/worker/`, `apps/web/`
- ✅ Builds Docker images for `linux/amd64` and `linux/arm64`
- ✅ Authenticates with GitHub Container Registry (GHCR)
- ✅ Pushes images to `ghcr.io/your-org/clipforge/{api,worker,web}`
- ✅ Scans with Trivy for vulnerabilities
- ✅ Reports security findings

### Troubleshooting

If workflow fails:

| Issue | Solution |
|-------|----------|
| "Permission denied" | Go to **Settings** → **Actions** → **General** → Enable "Allow GitHub Actions to create and approve pull requests" |
| "Branch doesn't match trigger" | Make sure you pushed to `main` or `develop` (workflow triggers on these branches) |
| "Image push failed" | GHCR automatically authenticates using `GITHUB_TOKEN`—no extra setup needed |

---

## Step 4: View Built Images in Packages

Once workflow completes successfully:

1. Go to your repository
2. Click **Packages** tab (right side)
3. You'll see three packages:
   - `api`
   - `worker`
   - `web`

4. Click each to see:
   - Image URI: `ghcr.io/your-org/clipforge/api`
   - Tags: `main`, `latest`, `main-a1b2c3d` (commit SHA)
   - Manifest for amd64 and arm64

### Pull Images

```bash
# Authenticate with GHCR (one-time)
echo ${{ secrets.GITHUB_TOKEN }} | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# Pull images
docker pull ghcr.io/your-org/clipforge/api:latest
docker pull ghcr.io/your-org/clipforge/worker:latest
docker pull ghcr.io/your-org/clipforge/web:latest

# Or use in docker-compose
docker-compose -f docker-compose.prod.yml pull
```

---

## Step 5: Deploy to Production

### Option A: Local Docker Compose (Single Server)

```bash
# 1. Set environment variables
export REGISTRY_URL=ghcr.io/YOUR_ORG/clipforge
export APP_VERSION=main  # or specific tag like 0.1.0

# 2. Copy and configure .env for production
cp .env.example .env
# Edit .env:
# - Change ENV=development to ENV=production
# - Set real SECRET_KEY (use strong random value)
# - Use production database URL if available
# - Set real LLM_API_KEY (Claude API key)
# - Configure production S3/R2 for object storage

# 3. Authenticate with GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# 4. Deploy
docker-compose -f docker-compose.prod.yml up -d

# 5. Verify
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f api
```

### Option B: Production Server (VPS/Cloud)

On your production server:

```bash
# 1. SSH into server
ssh user@your-server.com

# 2. Clone repository
git clone https://github.com/YOUR_USERNAME/clipforge.git
cd clipforge

# 3. Create production .env
cat > .env << EOF
ENV=production
SECRET_KEY=$(openssl rand -hex 32)
POSTGRES_USER=clipforge
POSTGRES_PASSWORD=$(openssl rand -hex 32)
POSTGRES_DB=clipforge
DATABASE_URL=postgresql://clipforge:PASSWORD@postgres:5432/clipforge
REDIS_URL=redis://redis:6379/0
S3_ENDPOINT_URL=https://r2.example.com
S3_ACCESS_KEY=your-r2-key
S3_SECRET_KEY=your-r2-secret
S3_BUCKET_SOURCE=clipforge-source
S3_BUCKET_RENDERED=clipforge-rendered
S3_PUBLIC_BASE_URL=https://cdn.example.com
LLM_API_KEY=your-claude-api-key
LLM_MODEL=claude-sonnet-4-6
NEXT_PUBLIC_API_BASE_URL=https://api.clipforge.example.com
EOF

# 4. Set registry and version
export REGISTRY_URL=ghcr.io/YOUR_ORG/clipforge
export APP_VERSION=main

# 5. Login and deploy
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# 6. Monitor
docker-compose -f docker-compose.prod.yml logs -f
```

### Option C: Kubernetes (Multi-Node, Advanced)

For scaling to multiple servers (future roadmap):

```bash
# Install ArgoCD for GitOps
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Create Helm values for ClipForge
# (Helm chart to be created in Phase 2)
```

---

## Step 6: Configure DNS & Reverse Proxy (Production)

### Using Nginx with Let's Encrypt

```nginx
server {
    listen 443 ssl http2;
    server_name api.clipforge.example.com;
    ssl_certificate /etc/letsencrypt/live/clipforge.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/clipforge.example.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 443 ssl http2;
    server_name clipforge.example.com;
    ssl_certificate /etc/letsencrypt/live/clipforge.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/clipforge.example.com/privkey.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Using Caddy (Simpler Alternative)

```caddy
api.clipforge.example.com {
    reverse_proxy localhost:8000
}

clipforge.example.com {
    reverse_proxy localhost:3000
}
```

---

## Step 7: Monitor & Maintain

### Check Service Status

```bash
# All services
docker-compose -f docker-compose.prod.yml ps

# Specific service logs
docker-compose -f docker-compose.prod.yml logs api
docker-compose -f docker-compose.prod.yml logs worker
docker-compose -f docker-compose.prod.yml logs web

# Stream logs (real-time)
docker-compose -f docker-compose.prod.yml logs -f
```

### View Security Scan Results

In GitHub:
1. Go to repository **Security** tab
2. Click **Code scanning alerts**
3. Review Trivy vulnerability reports

### Automatic Updates

Update images when new code is pushed:

```bash
# Option 1: Manual update
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# Option 2: Auto-update with Watchtower
docker run -d \
  --name watchtower \
  -v /var/run/docker.sock:/var/run/docker.sock \
  containrrr/watchtower \
  --interval 300 \
  clipforge-api \
  clipforge-worker \
  clipforge-web
```

---

## Step 8: Backup & Disaster Recovery

### Backup Postgres

```bash
# Manual backup
docker-compose exec postgres pg_dump -U clipforge clipforge > backup-$(date +%Y%m%d).sql

# Restore
cat backup-20250101.sql | docker-compose exec -T postgres psql -U clipforge clipforge
```

### Backup MinIO/S3 Data

```bash
# Sync to S3 backup bucket
aws s3 sync s3://clipforge-source s3://clipforge-backup-source
aws s3 sync s3://clipforge-rendered s3://clipforge-backup-rendered
```

---

## Next Steps

1. ✅ Push code to GitHub
2. ✅ Watch GitHub Actions build images
3. ✅ View images in Packages tab
4. ✅ Deploy with docker-compose.prod.yml
5. ⬜ Set up domain and SSL (Nginx/Caddy)
6. ⬜ Configure production environment (.env)
7. ⬜ Monitor and set up alerting (e.g., Prometheus/Grafana)
8. ⬜ Phase 2: OAuth + one-click publish
9. ⬜ Phase 3: Virality scoring + auto B-roll

---

## Useful Commands

```bash
# Check if services are healthy
curl http://localhost:8000/docs         # API Swagger
curl http://localhost:3000              # Web app
curl http://localhost:9001              # MinIO console

# View worker jobs
docker-compose exec worker python -m rq info

# View database
docker-compose exec postgres psql -U clipforge -d clipforge -c "\dt"

# Stop all services
docker-compose -f docker-compose.prod.yml down

# Remove all volumes (destructive!)
docker-compose -f docker-compose.prod.yml down -v
```

---

## Troubleshooting Deployment

### Images won't pull from GHCR

```bash
# Verify authentication
docker login ghcr.io

# Check image exists
docker pull ghcr.io/your-org/clipforge/api:latest

# If private, grant access in GitHub → Settings → Packages → Manage package access
```

### Services crash immediately

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs api

# Common issues:
# - Database not ready: wait for postgres healthcheck
# - Wrong environment variables: check .env
# - Port conflicts: ensure ports 8000, 3000, 5432, 6379 are available
```

### High memory usage

```bash
# Check memory
docker stats

# Increase limits in docker-compose.prod.yml:
# deploy:
#   resources:
#     limits:
#       memory: 8G
```

---

## Support & Documentation

- **GitHub Issues**: Report bugs at https://github.com/YOUR_USERNAME/clipforge/issues
- **Documentation**: See `DEPLOY.md`, `DOCKER_BUILD_CLOUD.md`, `REGISTRY_CICD_SETUP.md`
- **Docker Hub**: https://hub.docker.com
- **GHCR Docs**: https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry

---

**Ready to deploy?** Start with Option A (local Docker Compose) to test, then scale to Option B (VPS) or Option C (Kubernetes) for production. 🚀

