#!/usr/bin/env bash
OUT="/home/karim/smart-notebook/backend/scripts/result.txt"
cd /home/karim/smart-notebook
echo "=== Restarting backend ===" > "$OUT"
docker compose restart backend >> "$OUT" 2>&1
sleep 6
echo "" >> "$OUT"
echo "=== Login response ===" >> "$OUT"
curl -s -X POST 'http://localhost:8000/api/login' \
  -H 'Content-Type: application/json' \
  -d '{"email":"karim@yahoo.com","password":"test123"}' >> "$OUT" 2>&1
echo "" >> "$OUT"
