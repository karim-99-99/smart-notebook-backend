#!/usr/bin/env bash
# Run all 4 steps and write output to step-results.txt
cd /home/karim/smart-notebook
OUT="/home/karim/smart-notebook/backend/scripts/step-results.txt"
exec > "$OUT" 2>&1

echo "=== STEP 1: docker compose down / up -d ==="
docker compose down
docker compose up -d
sleep 10

echo ""
echo "=== STEP 2: auth.py first 5 lines in container ==="
docker exec sn_backend cat /app/app/routers/auth.py | head -5

echo ""
echo "=== STEP 3: curl login ==="
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
echo "=== DONE ==="
