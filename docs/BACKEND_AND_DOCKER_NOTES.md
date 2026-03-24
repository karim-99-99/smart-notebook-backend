# Backend, Docker, and login — notes

This file lives in the **backend** repository. Paths below assume this folder is the git root.

## Docker mount / “wrong” code in the container

**Cause:** The container sees whatever directory you mount. If you run `docker compose` from a different checkout (e.g. Windows path vs WSL path), you may mount a different copy of the code.

**Fix:** Always run compose from **this** backend repo directory (the one you edit):

```bash
cd /path/to/smart-notebook-backend   # your clone of the backend repo
docker compose up -d --build
```

**Quick check:**

```bash
docker exec sn_backend cat /app/app/routers/auth.py
```

---

## Login / `request.json()` (historical)

The login endpoint uses a **Pydantic body** (`LoginRequest`), not raw `await request.json()`, to avoid 500s from body handling edge cases.

---

## Layout (this repo only)

```
backend/   (repository root)
├── Dockerfile
├── docker-compose.yml       # Postgres + API; OCR is external (see .env.example)
├── docker-compose.prod.yml  # API only; DATABASE_URL + OCR_SERVICE_URL from env
├── requirements.txt
├── .env                     # not committed; copy from .env.example
├── render.yaml              # optional Render deploy
└── app/
    ├── main.py
    └── routers/
        ├── auth.py
        ├── notes.py
        └── ...
```

**OCR** lives in a separate repository. Run it locally or deploy it, then set `OCR_SERVICE_URL` in `.env` (see `.env.example`).

---

## Useful commands

```bash
# From this repo root (backend clone)
cp .env.example .env   # then edit .env
docker compose up -d --build

# Test login
curl -X POST 'http://localhost:8000/api/login' \
  -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","password":"yourpassword"}'
```
