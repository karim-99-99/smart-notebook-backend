#!/usr/bin/env bash
# Run from project root in WSL: bash backend/scripts/compare-auth-host-vs-container.sh
# This shows exactly what's on the host vs inside the container (and whether the volume mount is correct).

set -e
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

echo "=== 1. Project root (WSL) ==="
ls -la

echo ""
echo "=== 2. backend/app/routers/ (host) ==="
ls -la backend/app/routers/

echo ""
echo "=== 3. Host auth.py (first 35 lines) ==="
head -35 backend/app/routers/auth.py

echo ""
echo "=== 4. Container auth.py (first 35 lines) — same path as volume mount /app ==="
docker exec sn_backend cat /app/app/routers/auth.py | head -35

echo ""
echo "=== 5. If they differ, the volume mount may be wrong (e.g. Windows path vs WSL path). ==="
