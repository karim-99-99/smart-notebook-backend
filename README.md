# Smart Notebook — Backend API

FastAPI backend for the Smart Notebook mobile app. This folder is intended to be its **own GitHub repository** (separate from the OCR service and mobile app).

## Quick start (Docker)

1. Start the **OCR service** from the `smart-notebook-ocr` repo (`docker compose up` there on port **9000**), or set `OCR_SERVICE_URL` to a deployed OCR URL.
2. In **this** repo:

```bash
cp .env.example .env
# Edit .env if needed (JWT_SECRET, OCR_SERVICE_URL)
docker compose up -d --build
```

API: `http://localhost:8000`

- **Linux Docker** (no `host.docker.internal`): set `OCR_SERVICE_URL` in `.env` to `http://172.17.0.1:9000` or your host IP.

## Layout

```
./
├── app/                 # FastAPI app (routers, models, auth)
├── assets/fonts/        # Optional TTFs for Arabic PDF export
├── docs/                # Extra notes (e.g. Docker / login)
├── docker-compose.yml   # Postgres + API (OCR external)
├── docker-compose.prod.yml  # API only; use managed DB + external OCR
├── Dockerfile
├── render.yaml          # Optional Render deploy
└── requirements.txt
```

## Native Python (no Docker)

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
# Set DATABASE_URL, JWT_SECRET, OCR_SERVICE_URL in environment or .env
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Related repos

- **OCR**: PaddleOCR microservice — own repo, exposes port 9000.
- **Mobile**: React Native app — own repo (your Windows copy).

More detail: `docs/BACKEND_AND_DOCKER_NOTES.md`.
