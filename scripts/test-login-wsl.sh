#!/bin/bash
# Run from project root in WSL: ./backend/scripts/test-login-wsl.sh
# Or: bash backend/scripts/test-login-wsl.sh

set -e
cd "$(dirname "$0")/../.."
echo "Testing POST /api/login..."
curl -s -X POST 'http://localhost:8000/api/login' \
  -H 'Content-Type: application/json' \
  -d '{"email":"karim@yahoo.com","password":"test123"}'
echo ""
