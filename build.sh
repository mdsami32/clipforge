#!/bin/bash
set -e

# ClipForge Docker Build Script
# Supports local builds, Docker Build Cloud, and direct registry pushes

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REGISTRY="${REGISTRY_URL:-ghcr.io}"
VERSION="${APP_VERSION:-latest}"
PUSH="${PUSH:-false}"
PLATFORM="${PLATFORM:-linux/amd64,linux/arm64}"
BUILDER="${BUILDER:-default}"
USE_CLOUD="${USE_DOCKER_BUILD_CLOUD:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

usage() {
    cat << EOF
Usage: ./build.sh [OPTIONS]

Options:
    -r, --registry REGISTRY       Container registry URL (default: ghcr.io)
                                  Examples: docker.io/myorg, ghcr.io/myorg, AWS ECR URL
    -v, --version VERSION         Image version/tag (default: latest)
    -p, --push                    Push images to registry (default: false, build only)
    -m, --platform PLATFORMS      Comma-separated platforms (default: linux/amd64,linux/arm64)
                                  Options: linux/amd64, linux/arm64, linux/arm/v7
    -b, --builder BUILDER         Buildx builder name (default: default)
    -c, --cloud                   Use Docker Build Cloud
    -s, --service SERVICE         Build only one service (api, worker, or web)
    -h, --help                    Show this help message

Examples:
    # Build locally for current platform
    ./build.sh -v 0.1.0

    # Build for multiple platforms and push to GHCR
    ./build.sh -r ghcr.io/myorg/clipforge -v 0.1.0 -p

    # Use Docker Build Cloud for faster multi-platform builds
    ./build.sh -c -r ghcr.io/myorg/clipforge -v 0.1.0 -p

    # Build only the worker service
    ./build.sh -s worker -v 0.1.0 -p

    # Build for ARM64 only
    ./build.sh -m linux/arm64 -v 0.1.0 -p
EOF
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -r|--registry)
            REGISTRY="$2"
            shift 2
            ;;
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -p|--push)
            PUSH=true
            shift
            ;;
        -m|--platform)
            PLATFORM="$2"
            shift 2
            ;;
        -b|--builder)
            BUILDER="$2"
            shift 2
            ;;
        -c|--cloud)
            USE_CLOUD=true
            shift
            ;;
        -s|--service)
            SERVICE="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            log_error "Unknown option: $1"
            ;;
    esac
done

# Validate registry format
if [[ $REGISTRY == */ ]]; then
    REGISTRY="${REGISTRY%/}"
fi

# Check Docker and Buildx
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed"
fi

if ! docker buildx --version &> /dev/null; then
    log_error "Docker Buildx is not installed. Update Docker Desktop or install buildx"
fi

# Setup builder if using Docker Build Cloud
if [ "$USE_CLOUD" = true ]; then
    log_info "Configuring Docker Build Cloud..."
    if ! docker buildx use "$BUILDER" &> /dev/null; then
        log_warn "Builder '$BUILDER' not found, trying to create..."
        docker buildx create --driver cloud --name "$BUILDER" || log_error "Failed to create Docker Build Cloud builder"
    fi
    docker buildx use "$BUILDER"
    BUILDER_CMD="$BUILDER"
else
    BUILDER_CMD="${BUILDER:-default}"
fi

# Function to build and push image
build_image() {
    local service=$1
    local dockerfile=$2
    local context=$3
    local image_name="${REGISTRY}/$([ "$service" = "web" ] && echo "web" || echo "$service")"
    local image_tag="${image_name}:${VERSION}"
    local image_latest="${image_name}:latest"

    log_info "Building $service service..."
    log_info "Image: $image_tag"
    log_info "Platforms: $PLATFORM"
    log_info "Push: $PUSH"

    # Build command
    local build_cmd="docker buildx build"
    build_cmd="$build_cmd --platform $PLATFORM"
    build_cmd="$build_cmd -t $image_tag"
    
    if [ "$VERSION" != "latest" ]; then
        build_cmd="$build_cmd -t $image_latest"
    fi
    
    build_cmd="$build_cmd --file $dockerfile"
    
    if [ "$PUSH" = true ]; then
        build_cmd="$build_cmd --push"
    else
        # For local builds, only support current platform
        if [[ $PLATFORM == *","* ]]; then
            log_warn "Multi-platform builds without --push require Docker Build Cloud or buildx builder"
            log_info "Using single platform: linux/amd64"
            build_cmd="docker buildx build --platform linux/amd64 -t $image_tag --file $dockerfile"
        fi
    fi
    
    if [ "$USE_CLOUD" = true ]; then
        build_cmd="$build_cmd --builder $BUILDER_CMD"
    fi
    
    build_cmd="$build_cmd $context"

    log_info "Running: $build_cmd"
    eval "$build_cmd" || log_error "Failed to build $service"

    log_info "✓ $service build successful"
    echo ""
}

# Main build logic
log_info "=== ClipForge Docker Build ==="
log_info "Registry: $REGISTRY"
log_info "Version: $VERSION"
log_info "Docker Build Cloud: $USE_CLOUD"
echo ""

# Determine which services to build
SERVICES=("api" "worker" "web")
if [ ! -z "$SERVICE" ]; then
    if [[ ! " ${SERVICES[@]} " =~ " ${SERVICE} " ]]; then
        log_error "Unknown service: $SERVICE. Valid options: ${SERVICES[*]}"
    fi
    SERVICES=("$SERVICE")
fi

# Build each service
for service in "${SERVICES[@]}"; do
    case $service in
        api)
            build_image "api" "$SCRIPT_DIR/apps/api/Dockerfile" "$SCRIPT_DIR/apps/api"
            ;;
        worker)
            build_image "worker" "$SCRIPT_DIR/apps/worker/Dockerfile" "$SCRIPT_DIR/apps/worker"
            ;;
        web)
            build_image "web" "$SCRIPT_DIR/apps/web/Dockerfile.prod" "$SCRIPT_DIR/apps/web"
            ;;
    esac
done

log_info "=== Build Complete ==="
if [ "$PUSH" = true ]; then
    log_info "Images pushed to $REGISTRY"
    log_info "View at:"
    for service in "${SERVICES[@]}"; do
        echo "  - $REGISTRY/$service:$VERSION"
    done
else
    log_info "Images built locally (not pushed)"
    log_info "To push, add: --push flag"
fi
