# Docker Build Cloud Configuration

This file documents Docker Build Cloud setup for ClipForge.

## What is Docker Build Cloud?

Docker Build Cloud is a service that builds Docker images in the cloud, providing:
- **Multi-platform builds** (Linux, macOS, Windows) without manual setup
- **Shared caching** across team builds (faster rebuilds)
- **Managed infrastructure** (no need to manage your own build server)
- **Faster builds** by distributing work across Docker's cloud

## Prerequisites

1. Docker Desktop with paid plan OR Docker Build Cloud standalone subscription
2. `docker-buildx` (included in Docker Desktop 4.11+)
3. Docker CLI authenticated: `docker login`

## Quick Start

### 1. Create a Build Cloud Builder

```bash
# Create a new builder using Docker Build Cloud
docker buildx create \
  --driver cloud \
  --name my-cloud-builder

# Set it as default
docker buildx use my-cloud-builder

# Verify
docker buildx ls
```

Output should show:
```
NAME               DRIVER/ENDPOINT         STATUS   BUILDKIT   PLATFORMS
my-cloud-builder   docker-cloud://...     active   ...        linux/amd64,linux/arm64,linux/arm/v7,...
```

### 2. Build Multi-Platform Images

For ClipForge API:
```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t ghcr.io/your-org/clipforge/api:latest \
  --push \
  -f ./apps/api/Dockerfile \
  ./apps/api
```

For all services:
```bash
#!/bin/bash
REGISTRY="ghcr.io/your-org/clipforge"
VERSION=${1:-latest}

echo "Building API..."
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t $REGISTRY/api:$VERSION \
  -t $REGISTRY/api:latest \
  --push \
  -f ./apps/api/Dockerfile \
  ./apps/api

echo "Building Worker..."
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t $REGISTRY/worker:$VERSION \
  -t $REGISTRY/worker:latest \
  --push \
  -f ./apps/worker/Dockerfile \
  ./apps/worker

echo "Building Web..."
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t $REGISTRY/web:$VERSION \
  -t $REGISTRY/web:latest \
  --push \
  -f ./apps/web/Dockerfile.prod \
  ./apps/web

echo "All done!"
```

Save as `build-cloud.sh` and run:
```bash
chmod +x build-cloud.sh
./build-cloud.sh 0.1.0
```

### 3. GitHub Actions Integration

The included `.github/workflows/docker-build.yml` uses `docker/setup-buildx-action@v3`, which automatically:
- Detects Docker Build Cloud availability
- Uses it if your Docker credentials are available
- Falls back to local buildx if not

To explicitly enable Docker Build Cloud in GitHub Actions:

1. Add GitHub Secrets:
   - Go to **Settings** → **Secrets and variables** → **Actions**
   - Add `DOCKER_BUILD_CLOUD_TOKEN` (from Docker Hub account settings)

2. The workflow automatically uses it (no changes needed)

## Monitoring & Troubleshooting

### Check Build Cloud Status

```bash
# List all builders
docker buildx ls

# Inspect builder details
docker buildx inspect my-cloud-builder

# View build cache
docker buildx du --builder my-cloud-builder
```

### Debugging Failed Builds

```bash
# Add verbose output
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -v \
  --push \
  ...

# Load locally instead of pushing (for testing)
docker buildx build \
  --platform linux/amd64 \
  -t my-image:test \
  -f ./Dockerfile \
  .
```

### Common Issues

| Issue | Solution |
|-------|----------|
| "Failed to authenticate" | Run `docker login` and verify credentials |
| "Builder not found" | Create builder: `docker buildx create --driver cloud` |
| Build takes too long | Ensure `.dockerignore` excludes unnecessary files; check layer caching |
| "Push failed" | Verify registry credentials; check image tags match registry format |

## Cost & Quotas

- **Free tier**: 50 GB/month build cache
- **Paid**: $0.005 per build minute
- **Auto-cache pruning**: Old caches removed after 30 days of inactivity

Monitor usage:
```bash
docker buildx du --builder my-cloud-builder
```

## Best Practices

1. **Tag consistently**: Use semantic versioning (v0.1.0, v1.2.3)
   ```bash
   -t ghcr.io/org/clipforge/api:0.1.0 \
   -t ghcr.io/org/clipforge/api:latest \
   ```

2. **Use .dockerignore**: Reduces build context size (already set up)

3. **Multi-platform tagging**: Automatic with Docker BuildKit
   ```bash
   docker buildx build \
     --platform linux/amd64,linux/arm64 \
     -t my-image:latest \
     --push \
     .
   ```

4. **Cache strategy**:
   - GitHub Actions uses `type=gha` caching (already configured)
   - Docker Build Cloud shares cache across builds (built-in)

5. **Security**: Scan images before pushing
   ```bash
   docker scout cves ghcr.io/your-org/clipforge/api:latest
   ```

## Integration with CI/CD

The GitHub Actions workflow is pre-configured with:
- ✅ Multi-platform build support (`linux/amd64,linux/arm64`)
- ✅ GitHub Actions caching (`cache-from: type=gha`)
- ✅ Automatic Docker Build Cloud detection
- ✅ Trivy vulnerability scanning
- ✅ Metadata tagging (branch, semver, SHA, latest)

No additional configuration needed—just push to GitHub and the workflow handles the rest.

## More Information

- [Docker Build Cloud Docs](https://docs.docker.com/build-cloud/)
- [Buildx Documentation](https://docs.docker.com/build/architecture/)
- [Docker Buildx CLI Reference](https://docs.docker.com/reference/cli/docker/buildx/)

