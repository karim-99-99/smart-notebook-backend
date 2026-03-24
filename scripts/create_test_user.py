#!/usr/bin/env python3
"""
Create a test user in the backend so you can use the same account in both Supabase and FastAPI.

Default test account:
  email:    test@test.com
  password: TestPass123

Use when:
- Backend runs in Docker (DB is on localhost:5432 from host). Run from backend dir:
    POSTGRES_HOST=localhost python3 scripts/create_test_user.py
- Or call the API directly (backend must be running):
    curl -X POST http://localhost:8000/api/register -H "Content-Type: application/json" \\
      -d '{"email":"test@test.com","password":"TestPass123"}'

Then in the app: Sign up with test@test.com / TestPass123 (creates user in Supabase; backend
already has this user so register returns "already registered"). Then Log in with the same
credentials — both Supabase and backend will accept them.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if os.environ.get("POSTGRES_HOST") == "localhost" or os.environ.get("LIST_USERS_LOCALHOST"):
    u = os.environ.get("POSTGRES_USER", "kareem")
    p = os.environ.get("POSTGRES_PASSWORD", "secret123")
    n = os.environ.get("POSTGRES_DB", "smart_note")
    port = os.environ.get("POSTGRES_PORT", "5432")
    os.environ["DATABASE_URL"] = f"postgresql://{u}:{p}@localhost:{port}/{n}"

from app.database import SessionLocal
from app.models import User
from app.auth import hash_password

TEST_EMAIL = os.environ.get("TEST_USER_EMAIL", "test@test.com")
TEST_PASSWORD = os.environ.get("TEST_USER_PASSWORD", "TestPass123")


def main():
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == TEST_EMAIL).first()
        if existing:
            print(f"User already exists: {TEST_EMAIL}")
            print("You can use this account to log in (ensure the same email/password exists in Supabase).")
            return
        hashed = hash_password(TEST_PASSWORD)
        user = User(email=TEST_EMAIL, hashed_password=hashed)
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Created test user in backend: {TEST_EMAIL}")
        print(f"  Password: {TEST_PASSWORD}")
        print("")
        print("Next steps:")
        print("1. In the app, tap Sign up and register with the same email and password.")
        print("   (That creates the user in Supabase; backend will say already registered — that's OK.)")
        print("2. Then tap Log in with test@test.com / TestPass123.")
        print("3. Both Supabase and backend will accept the same account.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
