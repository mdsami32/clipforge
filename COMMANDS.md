# 📋 ClipForge: Copy-Paste Commands

Ready to push and deploy? Use these exact commands (replace placeholders in CAPS).

---

## 1️⃣ Create GitHub Repository

Go to https://github.com/new and fill in:
- **Repository name:** `clipforge`
- **Description:** Self-hosted alternative to Opus Clip
- **Visibility:** Public (or Private)
- Click **Create repository**

---

## 2️⃣ Push Code to GitHub

```bash
cd clipforge

git remote add origin https://github.com/YOUR_USERNAME/clipforge.git
git branch -M main
git push -u origin main
```

**Or with SSH** (if you have SSH keys):
```bash
git remote add origin git@github.com:YOUR_USERNAME/clipforge.git
git branch -M main
git push -u origin main
```

Replace:
- `YOUR_USERNAME` = your GitHub username

---

## 3️⃣ Monitor GitHub Actions Build

Open in browser:
```
https://github.com/YOUR_USERNAME/clipforge/actions
```

Watch the **Build and Push Docker Images** workflow run (~7 minutes).

---

## 4️⃣ View Built Images

Once workflow completes, go to:
```
https://github.com/YOUR_USERNAME/clipforge/packages
```

You'll see three packages:
- `api`
- `worker`
- `web`

---

## 5️⃣ Deploy Locally (Testing)

```bash
cd clipforge

# Set variables
export REGISTRY_URL=ghcr.io/YOUR_USERNAME/clipforge
export APP_VERSION=main

# Login to GHCR
echo YOUR_GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# Deploy
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps
```

Replace:
- `YOUR_USERNAME` = your GitHub username
- `YOUR_GITHUB_TOKEN` = your GitHub personal access token (create at https://github.com/settings/tokens)

**Access services:**
- Web: http://localhost:3000
- API: http://localhost:8000/docs
- MinIO: http://localhost:9001

---

## 6️⃣ Stop Deployment

```bash
docker-compose -f docker-compose.prod.yml down
```

---

## 7️⃣ Deploy to Production Server

SSH into your server and run:

```bash
# 1. SSH into server
ssh user@your-server.com

# 2. Clone repository
git clone https://github.com/YOUR_USERNAME/clipforge.git
cd clipforge

# 3. Create .env for production
cat > .env << 'EOF'
ENV=production
SECRET_KEY=$(openssl rand -hex 32)
POSTGRES_USER=clipforge
POSTGRES_PASSWORD=$(openssl rand -hex 32)
POSTGRES_DB=clipforge
DATABASE_URL=postgresql://clipforge:PASSWORD@postgres:5432/clipforge
REDIS_URL=redis://redis:6379/0
S3_ENDPOINT_URL=https://YOUR_S3_ENDPOINT
S3_ACCESS_KEY=YOUR_S3_KEY
S3_SECRET_KEY=YOUR_S3_SECRET
S3_BUCKET_SOURCE=clipforge-source
S3_BUCKET_RENDERED=clipforge-rendered
S3_PUBLIC_BASE_URL=https://YOUR_CDN_URL
LLM_API_KEY=YOUR_CLAUDE_API_KEY
NEXT_PUBLIC_API_BASE_URL=https://api.clipforge.example.com
EOF

# 4. Set variables
export REGISTRY_URL=ghcr.io/YOUR_USERNAME/clipforge
export APP_VERSION=main

# 5. Login to GHCR
echo YOUR_GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# 6. Pull and deploy
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# 7. Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

---

## 8️⃣ Setup Reverse Proxy (Nginx)

On your production server, create `/etc/nginx/sites-available/clipforge`:

```nginx
# HTTP redirect to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name clipforge.example.com api.clipforge.example.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS for Web App
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name clipforge.example.com;

    ssl_certificate /etc/letsencrypt/live/clipforge.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/clipforge.example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# HTTPS for API
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.clipforge.example.com;

    ssl_certificate /etc/letsencrypt/live/clipforge.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/clipforge.example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/clipforge /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 9️⃣ Setup SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot certonly --nginx -d clipforge.example.com -d api.clipforge.example.com

# Auto-renew
sudo systemctl enable certbot.timer
```

---

## 🔟 Verify Production Deployment

```bash
# Check all services running
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs

# Test API
curl https://api.clipforge.example.com/docs

# Test Web
curl https://clipforge.example.com
```

---

## 🔄 Update After Code Changes

When you make changes locally:

```bash
# 1. Make changes
# (edit files locally)

# 2. Commit and push
git add .
git commit -m "feat: add feature"
git push origin main

# 3. GitHub Actions builds automatically (~7 minutes)

# 4. Pull and redeploy (on your server)
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# 5. Verify
docker-compose -f docker-compose.prod.yml logs -f api
```

---

## 🆘 Troubleshooting Commands

```bash
# View all containers
docker ps

# View logs for specific service
docker logs CONTAINER_ID
docker-compose logs api
docker-compose logs -f worker

# Check memory usage
docker stats

# Remove all containers and volumes (DESTRUCTIVE!)
docker-compose down -v

# Restart a service
docker-compose restart api

# View environment variables
docker inspect CONTAINER_ID | grep -A 50 "Env"

# Check port is listening
netstat -tlnp | grep :8000
lsof -i :8000

# Test connectivity between services
docker-compose exec api curl http://postgres:5432
docker-compose exec worker redis-cli ping
```

---

## 📊 Monitoring Commands

```bash
# Real-time stats
docker stats

# View service health
docker-compose ps

# Follow logs in real-time
docker-compose logs -f

# Check specific service logs
docker-compose logs api --tail 50

# View network
docker network ls
docker network inspect clipforge_default

# Check volumes
docker volume ls
docker volume inspect clipforge_pgdata
```

---

## 🔐 Secrets Management

**Never commit .env to git!** It's in `.gitignore` by default.

To use environment variables:

```bash
# Create .env file (on production server)
cat > .env << EOF
SECRET_KEY=super-secret-key-$(openssl rand -hex 32)
POSTGRES_PASSWORD=secure-db-password-$(openssl rand -hex 32)
LLM_API_KEY=sk-your-claude-key
S3_SECRET_KEY=your-r2-secret-key
EOF

# Make it readable by Docker only
chmod 600 .env

# Load automatically when docker-compose runs
docker-compose -f docker-compose.prod.yml --env-file .env up -d
```

---

## 📈 Scale to Multiple Workers

In `docker-compose.prod.yml`:

```yaml
worker:
  deploy:
    replicas: 3  # Change from 2 to 3 (or more)
    resources:
      limits:
        cpus: '2'
        memory: 4G
```

Then:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

Docker will start 3 worker replicas sharing the same Redis queue.

---

## 🗑️ Cleanup

```bash
# Stop services (keep data)
docker-compose -f docker-compose.prod.yml down

# Remove everything (DESTRUCTIVE!)
docker-compose -f docker-compose.prod.yml down -v

# Clean up unused images
docker image prune -a

# Clean up unused volumes
docker volume prune

# Clean up everything
docker system prune -a
```

---

## 📝 Common Workflows

### Add a new feature (dev → prod)

```bash
# 1. Local development
docker-compose up --build

# 2. Test thoroughly

# 3. Commit and push
git add .
git commit -m "feat: new feature"
git push origin main

# 4. Wait for GitHub Actions (~7 min)

# 5. On production server
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### Rollback to previous version

```bash
# 1. Find previous tag
git log --oneline

# 2. Tag the previous version
git tag v0.1.0 PREVIOUS_COMMIT_SHA

# 3. Push tag
git push origin v0.1.0

# 4. GitHub Actions builds version 0.1.0

# 5. On production server
export APP_VERSION=0.1.0
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### Emergency restart

```bash
docker-compose -f docker-compose.prod.yml restart
```

### Tail all logs

```bash
docker-compose logs -f --timestamps
```

---

## 🎯 Success Checklist

```bash
# 1. Code pushed
git push -u origin main
# Expected: "Branch 'main' set up to track remote branch 'main' from 'origin'"

# 2. GitHub Actions running
open https://github.com/YOUR_USERNAME/clipforge/actions
# Expected: "Build and Push Docker Images" workflow in progress

# 3. Images built
# Wait ~7 minutes, then check:
docker pull ghcr.io/YOUR_USERNAME/clipforge/api:latest
# Expected: "Downloaded newer image for..."

# 4. Deployment started
docker-compose -f docker-compose.prod.yml up -d
# Expected: "Starting clipforge-api-1 ... done"

# 5. Services healthy
docker-compose -f docker-compose.prod.yml ps
# Expected: All services showing "healthy" or "Up"

# 6. Can access web app
curl http://localhost:3000
# Expected: HTML response

# 7. Can access API
curl http://localhost:8000/docs
# Expected: Swagger UI HTML

# 8. Database connected
docker-compose exec api python -c "from app.db import get_db; print('DB connected')"
# Expected: "DB connected"
```

---

## 🚀 You're Ready!

1. Replace placeholders (YOUR_USERNAME, YOUR_TOKEN, etc.)
2. Run commands in order
3. Watch GitHub Actions build
4. Deploy with one command
5. Enjoy! 🎉

**Questions?** Check the documentation files:
- `GITHUB_DEPLOYMENT.md` — Detailed guide
- `QUICKSTART.md` — Quick reference
- `ARCHITECTURE.md` — System design

