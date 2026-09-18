# Docker Registry & CI/CD Setup Guide

This guide walks you through pushing ClipForge images to a registry and setting up automated builds with GitHub Actions and Docker Build Cloud.

---

## Table of Contents

1. [GitHub Container Registry (Recommended)](#github-container-registry)
2. [Docker Hub](#docker-hub)
3. [Amazon ECR](#amazon-ecr)
4. [Docker Build Cloud](#docker-build-cloud)
5. [Local Testing](#local-testing)
6. [Production Deployment](#production-deployment)

---

## GitHub Container Registry

**GitHub Container Registry (GHCR)** is integrated with GitHub Actions and requires no separate credentials setup.

### Prerequisites
- GitHub repository (with this code pushed)
- GitHub Actions enabled (default in public repos)

### Automatic Setup (CI/CD Workflow)

The included `.github/workflows/docker-build.yml` is pre-configured for GHCR:

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Add Docker optimizations and CI/CD"
   git push origin main
   ```

2. **Workflow runs automatically** on:
   - Push to `main` or `develop` branches
   - Changes to `apps/api/`, `apps/worker/`, `apps/web/`, or workflow file
   - Manual trigger via GitHub Actions UI

3. **Images pushed to**:
   ```
   ghcr.io/your-org/clipforge/api:latest
   ghcr.io/your-org/clipforge/worker:latest
   ghcr.io/your-org/clipforge/web:latest
   ```

### Manual Push (One-time setup)

If you want to push manually before relying on CI/CD:

```bash
# Authenticate with GHCR
echo ${{ secrets.GITHUB_TOKEN }} | docker login ghcr.io -u ${{ github.actor }} --password-stdin

# Tag images (replace 'your-org' with your GitHub organization)
docker tag clipforge-api:latest ghcr.io/your-org/clipforge/api:latest
docker tag clipforge-worker:latest ghcr.io/your-org/clipforge/worker:latest
docker tag clipforge-web:latest ghcr.io/your-org/clipforge/web:latest

# Push
docker push ghcr.io/your-org/clipforge/api:latest
docker push ghcr.io/your-org/clipforge/worker:latest
docker push ghcr.io/your-org/clipforge/web:latest
```

### Make Images Public (Optional)

By default, GHCR images are private. To make them public:

1. Go to your repository → **Packages** tab
2. Click each package (api, worker, web)
3. **Package settings** → **Change visibility** → **Public**

---

## Docker Hub

### Prerequisites
- [Docker Hub account](https://hub.docker.com)
- Personal Access Token (not password)

### 1. Create GitHub Secrets

In your GitHub repository:
1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Add:
   - `DOCKERHUB_USERNAME` = your Docker Hub username
   - `DOCKERHUB_TOKEN` = your Personal Access Token

### 2. Modify Workflow

Update `.github/workflows/docker-build.yml`:

```yaml
env:
  REGISTRY: docker.io
  IMAGE_NAME_API: ${{ secrets.DOCKERHUB_USERNAME }}/clipforge-api
  IMAGE_NAME_WORKER: ${{ secrets.DOCKERHUB_USERNAME }}/clipforge-worker
  IMAGE_NAME_WEB: ${{ secrets.DOCKERHUB_USERNAME }}/clipforge-web
```

Change login step:

```yaml
- name: Log in to Docker Hub
  if: github.event_name != 'pull_request'
  uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKERHUB_USERNAME }}
    password: ${{ secrets.DOCKERHUB_TOKEN }}
```

### 3. Manual Push

```bash
# Authenticate
docker login

# Tag
docker tag clipforge-api:latest docker.io/your-username/clipforge-api:latest
docker tag clipforge-worker:latest docker.io/your-username/clipforge-worker:latest
docker tag clipforge-web:latest docker.io/your-username/clipforge-web:latest

# Push
docker push docker.io/your-username/clipforge-api:latest
docker push docker.io/your-username/clipforge-worker:latest
docker push docker.io/your-username/clipforge-web:latest
```

---

## Amazon ECR

### Prerequisites
- AWS account with ECR access
- AWS CLI installed and configured
- IAM user with ECR push permissions

### 1. Create ECR Repositories

```bash
aws ecr create-repository --repository-name clipforge/api --region us-east-1
aws ecr create-repository --repository-name clipforge/worker --region us-east-1
aws ecr create-repository --repository-name clipforge/web --region us-east-1
```

### 2. Create GitHub Secrets

Add to GitHub Secrets:
- `AWS_ACCOUNT_ID` = your AWS account ID
- `AWS_ACCESS_KEY_ID` = IAM access key
- `AWS_SECRET_ACCESS_KEY` = IAM secret key
- `AWS_REGION` = e.g., `us-east-1`

### 3. Modify Workflow

Replace the Docker login step:

```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    aws-region: ${{ secrets.AWS_REGION }}

- name: Login to Amazon ECR
  id: login-ecr
  uses: aws-actions/amazon-ecr-login@v2

- name: Set ECR image URIs
  id: ecr-uris
  run: |
    echo "api-uri=${{ steps.login-ecr.outputs.registry }}/clipforge/api" >> $GITHUB_OUTPUT
    echo "worker-uri=${{ steps.login-ecr.outputs.registry }}/clipforge/worker" >> $GITHUB_OUTPUT
    echo "web-uri=${{ steps.login-ecr.outputs.registry }}/clipforge/web" >> $GITHUB_OUTPUT
```

Update image references in build steps:

```yaml
tags: ${{ steps.ecr-uris.outputs.api-uri }}:latest,${{ steps.ecr-uris.outputs.api-uri }}:${{ github.sha }}
```

### 4. Manual Push

```bash
# Authenticate with ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Tag
docker tag clipforge-api:latest $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/clipforge/api:latest
docker tag clipforge-worker:latest $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/clipforge/worker:latest
docker tag clipforge-web:latest $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/clipforge/web:latest

# Push
docker push $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/clipforge/api:latest
docker push $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/clipforge/worker:latest
docker push $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/clipforge/web:latest
```

---

## Docker Build Cloud

**Docker Build Cloud** provides:
- **Faster multi-platform builds** (linux/amd64, linux/arm64, linux/arm/v7)
- **Shared caching** across builds
- **Pay-per-use** pricing (free tier available)

### Prerequisites
- Docker Desktop with paid plan or Docker Build Cloud subscription
- `docker-buildx` CLI tool

### 1. Set Up Docker Build Cloud

```bash
# Authenticate with Docker Hub
docker login

# Create a builder (or use default)
docker buildx create --driver cloud --name cloud-builder
docker buildx use cloud-builder

# Verify
docker buildx ls
```

### 2. Build Multi-Platform Images

```bash
# Build and push for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t ghcr.io/your-org/clipforge/api:latest \
  --push \
  ./apps/api

docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t ghcr.io/your-org/clipforge/worker:latest \
  --push \
  ./apps/worker

docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f ./apps/web/Dockerfile.prod \
  -t ghcr.io/your-org/clipforge/web:latest \
  --push \
  ./apps/web
```

### 3. GitHub Actions Integration

The included workflow already uses `docker/setup-buildx-action@v3`, which automatically uses Docker Build Cloud if available.

Enable in workflow by adding GitHub Secret:
- `DOCKER_BUILD_CLOUD_TOKEN` = your Docker Build Cloud token

---

## Local Testing

### Test the production compose file:

```bash
# Copy registry config
cp .env.registry.example .env.registry

# Edit and set your registry URL
# REGISTRY_URL=ghcr.io/your-org/clipforge

# Load environment (or edit .env directly)
source .env.registry  # or set in .env

# Pull and run locally
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up
```

### Test building locally (no push):

```bash
# Build all services (test only)
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f ./apps/api/Dockerfile \
  ./apps/api

docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f ./apps/worker/Dockerfile \
  ./apps/worker

docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f ./apps/web/Dockerfile.prod \
  ./apps/web
```

---

## Production Deployment

### Using Docker Compose

```bash
# Set registry and version
export REGISTRY_URL=ghcr.io/your-org/clipforge
export APP_VERSION=0.1.0

# Deploy
docker-compose -f docker-compose.prod.yml --env-file .env -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml --env-file .env -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Using Kubernetes (Next Step)

For scaling beyond single-host, use:
- **Helm** for chart-based deployments
- **Kustomize** for multi-environment overlays
- **Flux** or **ArgoCD** for GitOps

### Health Checks & Monitoring

All services in `docker-compose.prod.yml` have healthchecks defined. Monitor with:

```bash
# Watch health status
docker-compose -f docker-compose.prod.yml ps

# View logs for failed services
docker-compose -f docker-compose.prod.yml logs [service-name]
```

---

## Troubleshooting

### Images not building in GitHub Actions
- **Check**: Workflow file syntax with `docker/build-push-action@v5`
- **Check**: Branch name matches workflow trigger (`main` or `develop`)
- **Check**: GitHub Actions enabled in repository settings

### Login failures
- **GHCR**: Verify `GITHUB_TOKEN` has `packages:write` permission
- **Docker Hub**: Verify Personal Access Token, not password
- **AWS ECR**: Verify IAM policy allows `ecr:*` actions

### Multi-platform build errors
- **Check**: Docker Buildx supports your platform
- **Check**: `--platform` syntax is comma-separated (no spaces)
- **Fallback**: Build single platform with `docker build` instead of `buildx`

### Registry image too large
- **Reduce**: Ensure `.dockerignore` is properly excluding files
- **Compress**: Use multi-stage builds (already done)
- **Check**: No secrets/large files accidentally included

---

## Next Steps

1. ✅ Choose a registry (GHCR recommended for GitHub)
2. ✅ Push this code to GitHub
3. ✅ GitHub Actions workflow runs automatically
4. ✅ Images are built and pushed to registry
5. Deploy to production with `docker-compose.prod.yml`
6. Set up monitoring (Prometheus, Grafana, etc.)
7. Add rollback strategy for failed deployments

