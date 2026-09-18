# ClipForge Architecture & Deployment Flow

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        GitHub (Source Control)                          │
│  - Repository: github.com/YOUR_USERNAME/clipforge                       │
│  - Trigger: Push to main/develop branch                                 │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
                    (GitHub Actions detects push)
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│           GitHub Actions Workflow (.github/workflows/docker-build.yml)   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 1. Checkout code                                                │   │
│  │ 2. Setup Docker Buildx (multi-platform)                        │   │
│  │ 3. Login to GHCR (ghcr.io)                                     │   │
│  │ 4. Build for: linux/amd64 + linux/arm64                        │   │
│  │    - API (FastAPI)                                             │   │
│  │    - Worker (Python RQ)                                        │   │
│  │    - Web (Next.js)                                             │   │
│  │ 5. Push to GHCR                                                │   │
│  │ 6. Scan with Trivy (security)                                  │   │
│  │ 7. Upload results to GitHub Security tab                       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│              GitHub Container Registry (ghcr.io)                        │
│  - ghcr.io/your-org/clipforge/api:latest (365MB)                       │
│  - ghcr.io/your-org/clipforge/worker:latest (703MB)                    │
│  - ghcr.io/your-org/clipforge/web:latest (238MB)                       │
│  - Tags: main, develop, v0.1.0, latest, main-a1b2c3d                   │
│  - Platforms: amd64, arm64                                             │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
                    (Pull images & deploy)
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│         Production Deployment (docker-compose.prod.yml)                │
│  ┌─────────────┐  ┌──────────┐  ┌────────────┐  ┌──────────────┐       │
│  │  nginx/     │  │  Web     │  │  API       │  │  Worker      │       │
│  │  Caddy      │→→│  Next.js │→→│  FastAPI   │→→│  Python RQ   │       │
│  │  (reverse   │  │  :3000   │  │  :8000     │  │  Queue       │       │
│  │   proxy)    │  │          │  │            │  │              │       │
│  └─────────────┘  └──────────┘  └────────────┘  └──────────────┘       │
│        ↓                                               ↓                 │
│  ┌──────────────────┐  ┌──────────┐  ┌──────────┐    │                 │
│  │ SSL/TLS          │  │ Postgres │  │ Redis    │    │                 │
│  │ certificates     │  │ :5432    │  │ :6379    │    │                 │
│  │ (Let's Encrypt)  │  │ (DB)     │  │ (Queue)  │    │                 │
│  └──────────────────┘  └──────────┘  └──────────┘    │                 │
│                                                        ↓                 │
│                                                   ┌──────────┐           │
│                                                   │ MinIO    │           │
│                                                   │ :9000    │           │
│                                                   │ (S3)     │           │
│                                                   └──────────┘           │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                        End Users                                         │
│  - Web: https://clipforge.example.com (Next.js)                        │
│  - API: https://api.clipforge.example.com/docs (FastAPI Swagger)       │
│  - Upload/Download: HTTPS via reverse proxy                            │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Local Development Flow

```
┌──────────────────┐
│  Local Machine   │
│                  │
│  docker-compose  │
│  up --build      │
└────────────────┬─┘
                 ↓
┌──────────────────────────────────────────────────────────────────┐
│  docker-compose.yml (Development)                               │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐  ┌──────────────┐  │
│  │  Web     │  │  API     │  │  Worker    │  │  Postgres    │  │
│  │  :3000   │  │  :8000   │  │            │  │  :5432       │  │
│  │  (hot    │  │  (reload)│  │            │  │              │  │
│  │  reload) │  │          │  │            │  │              │  │
│  └──────────┘  └──────────┘  └────────────┘  └──────────────┘  │
│  ┌─────────────┬────────────┬──────────────┐                    │
│  │   Redis     │   MinIO    │   Services   │                    │
│  │   :6379     │  :9000/:9001              │                    │
│  └─────────────┴────────────┴──────────────┘                    │
│                                                                   │
│  Volumes (bind mounts for hot reload):                          │
│  - ./apps/api:/app                                              │
│  - ./apps/worker:/app                                           │
│  - ./apps/web:/app (+ node_modules mounting)                    │
└──────────────────────────────────────────────────────────────────┘
                       ↓
        Access at: http://localhost:3000
```

---

## CI/CD Pipeline Timeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Time   │ Event                      │ Status     │ Duration            │
├─────────┼────────────────────────────┼────────────┼─────────────────────┤
│ T+0s    │ git push origin main       │ Triggered  │ Instant             │
│ T+10s   │ GitHub detects push        │ Detected   │ Seconds             │
│ T+20s   │ Workflow starts            │ Running    │ Setup: 30-60s       │
│ T+90s   │ Docker build starts        │ Running    │ API: 40s            │
│         │                            │            │ Worker: 120s        │
│         │                            │            │ Web: 23s            │
│ T+300s  │ All builds complete        │ Complete   │ 5 minutes total     │
│ T+320s  │ Push to GHCR starts        │ Running    │ 20-30s              │
│ T+350s  │ Images pushed              │ Complete   │ 30s total           │
│ T+360s  │ Trivy scan starts          │ Running    │ 30-60s              │
│ T+420s  │ Scan complete              │ Complete   │ 1 minute            │
│ T+425s  │ Workflow complete          │ ✅ Success │ 7 minutes total     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Deployment Environments

### Development
```
Command:  docker-compose up --build
Port Mapping: Exposed to host (0.0.0.0)
Security: None (local only)
Hot Reload: Enabled (bind mounts)
Data: In-memory/local volumes
Use Case: Development, testing, debugging
```

### Production (Single Server)
```
Command:  docker-compose -f docker-compose.prod.yml up -d
Port Mapping: Localhost only (127.0.0.1), reverse proxy externally
Security: Hardened, health checks, resource limits
Hot Reload: Disabled
Data: Persistent volumes (database backups)
Use Case: Small to medium deployments (single VPS/server)
```

### Production (Kubernetes, Future)
```
Command:  kubectl apply -f k8s/deployment.yaml
Scaling: Horizontal (multiple replicas)
Load Balancer: Kubernetes ingress
Storage: Persistent volumes (EBS, NFS, etc.)
Use Case: Large-scale, high-availability deployments
```

---

## Build Strategy Comparison

| Strategy | Build Time | Multi-Platform | Cache | Cost | Best For |
|----------|-----------|----------------|-------|------|----------|
| Local (Docker) | 2-3 min | ❌ (current only) | ✅ | $0 | Dev, single platform |
| Local (Buildx) | 5-10 min | ✅ | ✅ | $0 | Dev, testing multi-platform |
| GitHub Actions | 5-10 min | ✅ | ✅ | $0 (free) | CI/CD, automated |
| Docker Build Cloud | 3-5 min | ✅ | ✅ | $0.005/min | Production, speed |

---

## File Organization

```
clipforge/
│
├── 🐳 Docker & Deployment
│   ├── docker-compose.yml                 # Dev environment
│   ├── docker-compose.prod.yml            # Production environment
│   ├── .dockerignore                      # Build context filter
│   ├── build.sh / build.bat               # Build scripts
│   │
│   ├── apps/api/
│   │   ├── Dockerfile                     # API image
│   │   ├── .dockerignore
│   │   └── (API source code)
│   │
│   ├── apps/worker/
│   │   ├── Dockerfile                     # Worker image (multi-stage)
│   │   ├── .dockerignore
│   │   └── (Worker source code)
│   │
│   └── apps/web/
│       ├── Dockerfile                     # Dev image
│       ├── Dockerfile.prod                # Prod image
│       ├── .dockerignore
│       ├── next.config.js                 # Standalone output
│       └── (Web source code)
│
├── 🔄 CI/CD Pipeline
│   └── .github/workflows/
│       └── docker-build.yml               # GitHub Actions workflow
│
├── 🚀 Deployment & Docs
│   ├── .env.example                       # Env template (dev)
│   ├── .env.registry.example              # Registry config template
│   ├── .gitignore                         # Git exclude rules
│   │
│   ├── IMPLEMENTATION_SUMMARY.md          # This summary
│   ├── GITHUB_DEPLOYMENT.md               # GitHub setup guide
│   ├── QUICKSTART.md                      # Quick reference
│   ├── DEPLOY.md                          # Deployment options
│   ├── DOCKER_OPTIMIZATION.md             # Technical details
│   ├── DOCKER_BUILD_CLOUD.md              # Build Cloud setup
│   ├── REGISTRY_CICD_SETUP.md             # Registry configuration
│   │
│   └── infra/
│       └── init.sql                       # Postgres schema
│
└── 📦 Application Code
    ├── apps/api/                          # FastAPI backend
    ├── apps/web/                          # Next.js frontend
    ├── apps/worker/                       # Python RQ workers
    └── packages/shared-types/             # TypeScript types
```

---

## Security Layers

```
┌──────────────────────────────────────────────────────────────────┐
│ GitHub Secrets & Credentials                                     │
│ - GITHUB_TOKEN (auto-provided for GHCR auth)                    │
│ - No manual secrets needed (GitHub manages auth)                │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ Artifact Scanning (Trivy)                                        │
│ - Scans all built images for CVEs                               │
│ - Reports to GitHub Security tab                                │
│ - Blocks high-severity vulnerabilities (future)                 │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ Registry Security (GHCR)                                         │
│ - Private images by default                                     │
│ - Fine-grained access control                                   │
│ - Image signing (future: sigstore)                              │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ Deployment Security                                              │
│ - .env with secrets (not committed to git)                      │
│ - SSL/TLS via reverse proxy (nginx/caddy)                       │
│ - Hardened docker-compose (localhost-only ports)                │
│ - Health checks (auto-restart failed services)                  │
│ - Resource limits (prevent DoS/OOM)                             │
└──────────────────────────────────────────────────────────────────┘
```

---

## Performance Optimization

### Build Optimization
- ✅ Layer caching (dependencies cached, code rebuilds faster)
- ✅ Multi-stage builds (separates build and runtime)
- ✅ .dockerignore (reduces build context by ~90%)
- ✅ Docker Build Cloud (parallel builds, shared cache)

### Runtime Optimization
- ✅ Persistent volumes (Redis AOF, Postgres)
- ✅ Health checks (auto-restart failed services)
- ✅ Resource limits (prevent runaway processes)
- ✅ Next.js standalone output (smaller images, faster startup)

### Network Optimization
- ✅ Service-to-service communication via Docker DNS
- ✅ Reverse proxy (nginx/caddy) for SSL/compression
- ✅ Multi-platform images (native performance on different architectures)

---

## Monitoring & Observability (Future)

```
┌────────────────────────────────────────────────────────┐
│ Monitoring Stack (To implement in Phase 2+)            │
│                                                         │
│ ┌─────────────┐  ┌─────────────┐  ┌──────────────┐   │
│ │ Prometheus  │→→│ Grafana     │  │ AlertManager │   │
│ │ (metrics)   │  │ (dashboard) │→→│ (alerts)     │   │
│ └─────────────┘  └─────────────┘  └──────────────┘   │
│                                         ↓              │
│                                   ┌──────────────┐    │
│                                   │ Slack/Email  │    │
│                                   │ (notified)   │    │
│                                   └──────────────┘    │
│                                                         │
│ Logging Stack:                                         │
│ ┌─────────────┐  ┌──────────┐  ┌──────────────┐     │
│ │ Docker Logs │→→│ Filebeat │→→│ ELK Stack    │     │
│ │             │  │          │  │ (centralized)│     │
│ └─────────────┘  └──────────┘  └──────────────┘     │
│                                                         │
│ Tracing:                                              │
│ ┌──────────────────┐  ┌─────────────────────┐       │
│ │ OpenTelemetry    │→→│ Jaeger/Zipkin       │       │
│ │ (request trace)  │  │ (visualization)     │       │
│ └──────────────────┘  └─────────────────────┘       │
└────────────────────────────────────────────────────────┘
```

---

## Cost Breakdown

| Component | Cost | Notes |
|-----------|------|-------|
| GitHub (repo + Actions) | Free | 2000 min/month free tier |
| GHCR (registry) | Free | Unlimited storage |
| Docker Build Cloud | Free tier | $0.005/min after free allotment |
| VPS (1GB RAM, 20GB disk) | $5-10/mo | Hetzner, DigitalOcean, Linode |
| S3/R2 (object storage) | $0.015/GB | Cloudflare R2 cheaper than AWS S3 |
| Database backup | $5-20/mo | AWS RDS or managed DB |
| CDN (optional) | $0.1/GB | Cloudflare, AWS CloudFront |
| **Total** | **~$10-30/mo** | For small to medium deployment |

---

## Success Metrics

- ✅ **Build time:** < 10 minutes (first), < 3 minutes (cached)
- ✅ **Image push:** < 5 minutes to GHCR
- ✅ **Deployment:** < 2 minutes to start services
- ✅ **Health checks:** All services pass within 30 seconds
- ✅ **Security:** Zero high-severity CVEs
- ✅ **Uptime:** 99.9% (health checks + auto-restart)
- ✅ **Performance:** API response < 200ms, Web load < 2s

---

## Next Steps

1. ✅ **Push to GitHub** → `git push -u origin main`
2. ✅ **Watch workflow** → GitHub Actions builds & pushes images
3. ✅ **View images** → Check Packages tab in GitHub
4. ✅ **Deploy locally** → `docker-compose.prod.yml up -d`
5. ⬜ **Configure domain** → Point DNS to server
6. ⬜ **Setup reverse proxy** → nginx/caddy with SSL
7. ⬜ **Setup monitoring** → Prometheus + Grafana (future)
8. ⬜ **Enable backups** → Database + S3 snapshots
9. ⬜ **Document runbook** → Operational procedures

---

**You're ready to deploy!** 🚀

Push your code to GitHub and watch the magic happen. Images will be built, scanned, and ready to deploy in under 10 minutes.

