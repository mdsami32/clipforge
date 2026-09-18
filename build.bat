@echo off
REM ClipForge Docker Build Script (Windows)
REM Supports local builds, Docker Build Cloud, and direct registry pushes

setlocal enabledelayedexpansion

REM Default values
set "REGISTRY=%REGISTRY_URL%"
if "!REGISTRY!"=="" set "REGISTRY=ghcr.io"
set "VERSION=%APP_VERSION%"
if "!VERSION!"=="" set "VERSION=latest"
set "PUSH=false"
set "PLATFORM=linux/amd64,linux/arm64"
set "BUILDER=default"
set "USE_CLOUD=false"

REM Parse arguments
:parse_args
if "%1"=="" goto main
if "%1"=="-r" (
    set "REGISTRY=%2"
    shift & shift
    goto parse_args
)
if "%1"=="--registry" (
    set "REGISTRY=%2"
    shift & shift
    goto parse_args
)
if "%1"=="-v" (
    set "VERSION=%2"
    shift & shift
    goto parse_args
)
if "%1"=="--version" (
    set "VERSION=%2"
    shift & shift
    goto parse_args
)
if "%1"=="-p" (
    set "PUSH=true"
    shift
    goto parse_args
)
if "%1"=="--push" (
    set "PUSH=true"
    shift
    goto parse_args
)
if "%1"=="-m" (
    set "PLATFORM=%2"
    shift & shift
    goto parse_args
)
if "%1"=="--platform" (
    set "PLATFORM=%2"
    shift & shift
    goto parse_args
)
if "%1"=="-b" (
    set "BUILDER=%2"
    shift & shift
    goto parse_args
)
if "%1"=="--builder" (
    set "BUILDER=%2"
    shift & shift
    goto parse_args
)
if "%1"=="-c" (
    set "USE_CLOUD=true"
    shift
    goto parse_args
)
if "%1"=="--cloud" (
    set "USE_CLOUD=true"
    shift
    goto parse_args
)
if "%1"=="-s" (
    set "SERVICE=%2"
    shift & shift
    goto parse_args
)
if "%1"=="--service" (
    set "SERVICE=%2"
    shift & shift
    goto parse_args
)
if "%1"=="-h" (
    goto help
)
if "%1"=="--help" (
    goto help
)

:main
REM Validate Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed or not in PATH
    exit /b 1
)

REM Validate Buildx
docker buildx --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Buildx is not installed
    exit /b 1
)

REM Setup builder if using Docker Build Cloud
if "!USE_CLOUD!"=="true" (
    echo [INFO] Configuring Docker Build Cloud...
    docker buildx use !BUILDER! >nul 2>&1
    if errorlevel 1 (
        echo [WARN] Builder '!BUILDER!' not found, attempting to create...
        docker buildx create --driver cloud --name !BUILDER!
        if errorlevel 1 (
            echo [ERROR] Failed to create Docker Build Cloud builder
            exit /b 1
        )
    )
)

echo [INFO] === ClipForge Docker Build ===
echo [INFO] Registry: !REGISTRY!
echo [INFO] Version: !VERSION!
echo [INFO] Docker Build Cloud: !USE_CLOUD!
echo [INFO] Push: !PUSH!
echo.

REM Build services
if "!SERVICE!"=="" (
    call :build_service api
    call :build_service worker
    call :build_service web
) else (
    call :build_service !SERVICE!
)

echo [INFO] === Build Complete ===
if "!PUSH!"=="true" (
    echo [INFO] Images pushed to !REGISTRY!
) else (
    echo [INFO] Images built locally ^(not pushed^)
    echo [INFO] To push, add: --push flag
)
exit /b 0

:build_service
setlocal
set "service=%1"
set "image_name=!REGISTRY!/!service!"
set "image_tag=!image_name!:!VERSION!"
set "image_latest=!image_name!:latest"

echo [INFO] Building !service! service...
echo [INFO] Image: !image_tag!
echo [INFO] Platforms: !PLATFORM!

REM Build command
set "build_cmd=docker buildx build"
set "build_cmd=!build_cmd! --platform !PLATFORM!"
set "build_cmd=!build_cmd! -t !image_tag!"

if not "!VERSION!"=="latest" (
    set "build_cmd=!build_cmd! -t !image_latest!"
)

if "!service!"=="web" (
    set "build_cmd=!build_cmd! -f apps\web\Dockerfile.prod"
) else (
    set "build_cmd=!build_cmd! -f apps\!service!\Dockerfile"
)

if "!PUSH!"=="true" (
    set "build_cmd=!build_cmd! --push"
)

if "!USE_CLOUD!"=="true" (
    set "build_cmd=!build_cmd! --builder !BUILDER!"
)

set "build_cmd=!build_cmd! apps\!service!"

echo [INFO] Running: !build_cmd!
!build_cmd!
if errorlevel 1 (
    echo [ERROR] Failed to build !service!
    exit /b 1
)

echo [INFO] ✓ !service! build successful
echo.
endlocal
exit /b 0

:help
echo Usage: build.bat [OPTIONS]
echo.
echo Options:
echo    -r, --registry REGISTRY       Container registry URL (default: ghcr.io)
echo                                  Examples: docker.io/myorg, ghcr.io/myorg
echo    -v, --version VERSION         Image version/tag (default: latest)
echo    -p, --push                    Push images to registry (default: false, build only)
echo    -m, --platform PLATFORMS      Comma-separated platforms
echo                                  (default: linux/amd64,linux/arm64)
echo    -b, --builder BUILDER         Buildx builder name (default: default)
echo    -c, --cloud                   Use Docker Build Cloud
echo    -s, --service SERVICE         Build only one service (api, worker, or web)
echo    -h, --help                    Show this help message
echo.
echo Examples:
echo    REM Build locally for current platform
echo    build.bat -v 0.1.0
echo.
echo    REM Build for multiple platforms and push to GHCR
echo    build.bat -r ghcr.io/myorg/clipforge -v 0.1.0 -p
echo.
echo    REM Use Docker Build Cloud
echo    build.bat -c -r ghcr.io/myorg/clipforge -v 0.1.0 -p
exit /b 0
