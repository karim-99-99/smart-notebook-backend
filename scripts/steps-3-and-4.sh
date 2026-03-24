#!/usr/bin/env bash
# Run from project root in WSL: bash backend/scripts/steps-3-and-4.sh
# Step 3: Test login
# Step 4: Add missing column and user (after compose down resets DB)

set -e
cd "$(dirname "$0")/../.."

echo "=== STEP 3: Test login ==="
curl -s -X POST 'http://localhost:8000/api/login' \
  -H 'Content-Type: application/json' \
  -d '{"email":"karim@yahoo.com","password":"test123"}'
echo ""

echo ""
echo "=== STEP 4: Add column and user ==="
docker exec sn_postgres psql -U kareem -d smart_note -c "
ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
INSERT INTO users (email, hashed_password) VALUES ('karim@yahoo.com', '\$2b\$12\$3dxZhWTn8UdimpX9S1NaQun93Pg.jAzo9yZZNtzm15oy82yAOKWte') ON CONFLICT (email) DO NOTHING;
"

echo ""
echo "=== STEP 3 again (after user exists) ==="
curl -s -X POST 'http://localhost:8000/api/login' \
  -H 'Content-Type: application/json' \
  -d '{"email":"karim@yahoo.com","password":"test123"}'
echo ""
