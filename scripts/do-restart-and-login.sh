#!/usr/bin/env bash
# Run in WSL from project root: bash backend/scripts/do-restart-and-login.sh
set -e
cd "$(dirname "$0")/../.."
echo "Restarting backend..."
docker compose restart backend
sleep 6
echo "Testing login..."
curl -s -X POST 'http://localhost:8000/api/login' -H 'Content-Type: application/json' -d '{"email":"karim@yahoo.com","password":"test123"}'
echo ""
echo "Done."
