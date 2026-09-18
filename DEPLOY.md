# ClipForge Deployment & Registry Guide

Quick-start guide for pushing ClipForge images to a container registry and deploying with CI/CD.

## 🚀 Quick Start (GitHub Actions)

### Automatic (Recommended)

1. Push code to GitHub:
   ```bash
   git add .
   git commit -m "Add Docker optimizations and CI/CD"
   git push origin main
   ```

2. GitHub Actions automatically:
   - Builds images for `linux/amd64` and `linux/arm64`
   - Pushes to GitHub Container Registry (ghcr.io)
   - Scans for vulnerabilities with Trivy
   - Tags images with branch name, version, and commit SHA

3. View images in your GitHub repository:
   - Go to **Packages** tab
   - Images available as `ghcr.io/your-org/clipforge/{api,worker,web}`

### Manual Push (Local)

```bash
# 1. Authenticate with GitHub Container Registry
echo $YOUR_GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# 2. Tag images
docker tag clipforge-api:latest ghcr.io/your-org/clipforge/api:0.1.0
docker tag clipforge-worker:latest ghcr.io/your-org/clipforge/worker:0.1.0
docker tag clipforge-web:latest ghcr.io/your-org/clipforge/web:0.1.0

# 3. Push
docker push ghcr.io/your-org/clipforge/api:0.1.0
docker push ghcr.io/your-org/clipforge/worker:0.1.0
docker push ghcr.io/your-org/clipforge/web:0.1.0
```

## 📦 Build Script (All Platforms)

Use the included build script for consistent builds across dev, CI/CD, and production.

### Linux/macOS

```bash
# Make executable
chmod +x build.sh

# Build locally (current platform only)
./build.sh -v 0.1.0

# Build for multiple platforms (requires Docker Build Cloud or buildx)
./build.sh -p -r ghcr.io/your-org/clipforge -v 0.1.0

# Build only one service
./build.sh -s worker -v 0.1.0 -p

# Use Docker Build Cloud for faster multi-platform builds
./build.sh -c -p -r ghcr.io/your-org/clipforge -v 0.1.0
```

### Windows

```cmd
# Build locally
build.bat -v 0.1.0

# Build and push
build.bat -r ghcr.io/your-org/clipforge -v 0.1.0 -p

# Use Docker Build Cloud
build.bat -c -r ghcr.io/your-org/clipforge -v 0.1.0 -p
```

## 🔐 Registry Options

### GitHub Container Registry (Recommended for GitHub)

**Pros:**
- Integrated with GitHub Actions
- Free public/private storage
- No separate authentication needed for CI/CD

**Setup:**
- GitHub Actions workflow pre-configured
- Just push code to GitHub

**Manual push:**
```bash
docker login ghcr.io -u USERNAME
docker tag clipforge-api:latest ghcr.io/your-org/clipforge/api:latest
docker push ghcr.io/your-org/clipforge/api:latest
```

### Docker Hub

**Pros:**
- Public registry, easy sharing
- Good for open-source projects

**Setup:**
1. Create account at hub.docker.com
2. Create Personal Access Token (Settings → Security)
3. Add GitHub Secrets: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`
4. Modify workflow (see `REGISTRY_CICD_SETUP.md`)

**Manual push:**
```bash
docker login docker.io
docker tag clipforge-api:latest docker.io/your-username/clipforge-api:latest
docker push docker.io/your-username/clipforge-api:latest
```

### Amazon ECR

**Setup:**
```bash
aws ecr create-repository --repository-name clipforge/api --region us-east-1
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

docker tag clipforge-api:latest $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/clipforge/api:latest
docker push $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/clipforge/api:latest
```

## 📊 Docker Build Cloud

For faster multi-platform builds (linux/amd64, linux/arm64):

```bash
# 1. Create Docker Build Cloud builder
docker buildx create --driver cloud --name clipforge-builder

# 2. Use in build script
./build.sh -c -r ghcr.io/your-org/clipforge -v 0.1.0 -p

# Or manually
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t ghcr.io/your-org/clipforge/api:0.1.0 \
  --push \
  --builder clipforge-builder \
  ./apps/api
```

See `DOCKER_BUILD_CLOUD.md` for details.

## 🚢 Deploy to Production

### Using Docker Compose

```bash
# 1. Set registry and version
export REGISTRY_URL=ghcr.io/your-org/clipforge
export APP_VERSION=0.1.0

# 2. Copy production env
cp .env.example .env
# Edit .env for production (secrets, URLs, etc.)

# 3. Pull latest images
docker-compose -f docker-compose.prod.yml pull

# 4. Start services
docker-compose -f docker-compose.prod.yml up -d

# 5. Check status
docker-compose -f docker-compose.prod.yml ps
```

### Using Kubernetes

For multi-node deployments, use Kubernetes manifests (TODO):

```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

## 📋 CI/CD Workflow

### What GitHub Actions Does Automatically

On every push to `main` or `develop`:

1. ✅ Detects changes to `apps/api/`, `apps/worker/`, or `apps/web/`
2. ✅ Builds for `linux/amd64` and `linux/arm64`
3. ✅ Tags with:
   - Branch name (e.g., `main`, `develop`)
   - Semantic version if tagged (e.g., `v0.1.0`)
   - Commit SHA (e.g., `main-a1b2c3d`)
   - `latest` (if pushing to main branch)
4. ✅ Pushes to `ghcr.io/your-org/clipforge/{api,worker,web}`
5. ✅ Scans with Trivy for vulnerabilities
6. ✅ Reports security findings in GitHub Security tab

### Trigger Manually

In GitHub repository:
1. Go to **Actions** tab
2. Select **Build and Push Docker Images**
3. Click **Run workflow**
4. Choose branch
5. Click **Run workflow**

### View Build Results

1. **Actions** tab → **Build and Push Docker Images**
2. Click run to see logs
3. Check **Packages** tab for published images

## 🔒 Security

### Scan Images Locally

```bash
# Install trivy
brew install trivy  # macOS
# or download from https://github.com/aquasecurity/trivy

# Scan image
trivy image ghcr.io/your-org/clipforge/api:latest

# View vulnerabilities
docker scout cves ghcr.io/your-org/clipforge/api:latest
```

### View Scan Results in GitHub

1. Go to repository **Security** tab
2. Click **Code scanning alerts** (if vulnerabilities found)
3. Review Trivy scan results from workflow runs

## 🐛 Troubleshooting

### Push to Registry Fails

```bash
# Verify authentication
docker login ghcr.io
docker pull ghcr.io/your-org/clipforge/api:latest

# Check image exists locally
docker images | grep clipforge

# Manually tag and push
docker tag clipforge-api:latest ghcr.io/your-org/clipforge/api:latest
docker push ghcr.io/your-org/clipforge/api:latest
```

### GitHub Actions Build Fails

1. Go to **Actions** → **Build and Push Docker Images**
2. Click failed run
3. Expand step to see error
4. Common issues:
   - Branch name not `main` or `develop` (check workflow trigger)
   - Missing `.dockerignore` (already added)
   - Dockerfile syntax error (rare, pre-checked)

### Image Too Large

```bash
# Check image size
docker images | grep clipforge

# Verify .dockerignore is working
docker build --no-cache --progress=plain ./apps/api 2>&1 | grep -i "ignoring\|sending"

# Reduce .dockerignore entries (keep essentials only)
# Rebuild with: docker build --no-cache ./apps/api
```

### Multi-Platform Build Not Working

```bash
# Verify Buildx is available
docker buildx ls

# Check if builder supports multiple platforms
docker buildx inspect default

# If not, create cloud builder
docker buildx create --driver cloud --name clipforge

# Or use local buildx (Linux only)
docker run --privileged tonistiigi/binfmt:latest --install all
```

## 📚 Additional Resources

- [GitHub Actions Docker Build](https://github.com/docker/build-push-action)
- [Docker Buildx Documentation](https://docs.docker.com/build/)
- [Docker Build Cloud](https://docs.docker.com/build-cloud/)
- [Trivy Vulnerability Scanner](https://aquasecurity.github.io/trivy/)

## 📝 Configuration Files

- `.github/workflows/docker-build.yml` — GitHub Actions CI/CD
- `docker-compose.prod.yml` — Production deployment
- `.env.registry.example` — Registry configuration template
- `build.sh` / `build.bat` — Build scripts
- `REGISTRY_CICD_SETUP.md` — Detailed setup guide
- `DOCKER_BUILD_CLOUD.md` — Docker Build Cloud guide

---

**Next Step:** Push code to GitHub and watch the workflow run! 🎉

