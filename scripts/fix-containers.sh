#!/bin/bash
# Fix container conflicts - run this before docker compose up

echo "Removing conflicting containers..."

# Remove all smart-notebook containers by name
docker rm -f sn_postgres sn_backend sn_ocr_service 2>/dev/null

# Remove by the specific ID if it still exists
docker rm -f 9101876bad33029024d0a953814759b6867b8cda3ef2fcbd30028e5080a18b57 2>/dev/null

# Clean up with docker compose
docker compose down 2>/dev/null

# Remove all stopped containers
docker container prune -f

echo "✅ All conflicts cleared! Now run: docker compose up"
