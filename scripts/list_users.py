#!/usr/bin/env python3
"""
List all users in the backend database (email, id, created_at).
Use this to compare with Supabase Auth → Users so the same account exists in both.

Run from backend directory with dependencies installed (use the same env as the API):

  # Activate venv and install deps if needed:
  cd backend
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt

  # If the DB runs in Docker, use localhost from the host (ensure DB port is exposed, e.g. docker compose up -d db):
  POSTGRES_HOST=localhost python3 scripts/list_users.py
"""
import os
import sys

# Allow importing app when run as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# If you run from host while DB is in Docker, .env has DATABASE_URL with host "db".
# Set DATABASE_URL to localhost before app.database loads so load_dotenv() won't override.
if os.environ.get("POSTGRES_HOST") == "localhost" or os.environ.get("LIST_USERS_LOCALHOST"):
    u = os.environ.get("POSTGRES_USER", "kareem")
    p = os.environ.get("POSTGRES_PASSWORD", "secret123")
    n = os.environ.get("POSTGRES_DB", "smart_note")
    port = os.environ.get("POSTGRES_PORT", "5432")
    os.environ["DATABASE_URL"] = f"postgresql://{u}:{p}@localhost:{port}/{n}"

from app.database import SessionLocal
from app.models import User


def main():
    db = SessionLocal()
    try:
        users = db.query(User).order_by(User.id).all()
        if not users:
            print("No users in backend database.")
            return
        print("Backend users (compare with Supabase Dashboard → Authentication → Users):")
        print("-" * 60)
        for u in users:
            print(f"  id={u.id}  email={u.email}  created_at={u.created_at}")
        print("-" * 60)
        print(f"Total: {len(users)} user(s)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
