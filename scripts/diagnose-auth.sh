#!/usr/bin/env bash
# Run from project root: bash backend/scripts/diagnose-auth.sh
# Writes to backend/scripts/diagnose-output.txt
set -e
cd "$(dirname "$0")/../.."
OUT="backend/scripts/diagnose-output.txt"
echo "=== 1. auth.py in container ===" > "$OUT"
docker exec sn_backend cat /app/app/routers/auth.py >> "$OUT" 2>&1
echo "" >> "$OUT"
echo "=== 2. Registered paths (openapi.json) ===" >> "$OUT"
curl -s http://localhost:8000/openapi.json | python3 -c "
import json,sys
d=json.load(sys.stdin)
for path in d['paths']:
    print(path)
" >> "$OUT" 2>&1
echo "" >> "$OUT"
echo "=== 3. auth router import and routes ===" >> "$OUT"
docker exec sn_backend python3 -c "
import traceback
try:
    from app.routers.auth import router
    print('Routes:')
    for r in router.routes:
        print(' ', r.methods, r.path)
except Exception as e:
    traceback.print_exc()
" >> "$OUT" 2>&1
echo "Done. Output in $OUT"
