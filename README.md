# AI-Powered Code Review Assistant

A production-oriented starter for reviewing submitted Python code using Ruff, Bandit, and an optional AI provider. Includes FastAPI, PostgreSQL, JWT authentication, Argon2 password hashing, GitHub webhook signature verification, Docker Compose, tests, and a small React/TypeScript UI.

> Security and deployment note: this is a runnable baseline, not a substitute for a security review. Before public production use, configure secrets, TLS, database backups, rate limits at the edge, monitoring, and review the threat model. AI findings are advisory and can be wrong.

## Architecture

- `backend/app/api`: HTTP endpoints
- `backend/app/core`: settings, auth, security
- `backend/app/db`: SQLAlchemy session and models
- `backend/app/schemas`: request/response validation
- `backend/app/services`: orchestration, analyzers, AI providers
- `frontend`: React + TypeScript UI
- `tests`: backend tests
- `.github/workflows/ci.yml`: automated checks

## Quick start (Docker)

1. Copy `.env.example` to `.env` and replace every secret.
2. Start services:

   ```bash
   docker compose up --build
   ```

3. API docs: http://localhost:8000/docs
4. Frontend: http://localhost:5173

The first database tables are created on startup for convenience. For a stricter production deployment, replace startup table creation with Alembic migrations before schema changes are deployed.

The GitHub webhook endpoint verifies HMAC SHA-256 signatures. It intentionally does not yet fetch pull-request diffs or publish review comments; those require GitHub App credentials, permissions, and a PR processing worker.

## Local development without Docker

Run the backend in one terminal and the frontend in another. The Vite development server proxies `/api` and `/health` to `http://127.0.0.1:8000`.

Backend (Python 3.12 recommended):

```bash
cd backend
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Git Bash: source .venv/Scripts/activate
pip install -r requirements.txt
copy ..\.env.example ..\.env  # Windows; on macOS/Linux: cp ../.env.example ../.env
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Set `DATABASE_URL` to a local PostgreSQL URL for local development. For a quick isolated test run, `sqlite+pysqlite:///./dev.db` is supported.

## AI provider configuration

Set `AI_PROVIDER` to `ollama`, `openai`, `anthropic`, or `disabled`.
- Ollama: set `OLLAMA_BASE_URL` and `OLLAMA_MODEL`.
- OpenAI: set `OPENAI_API_KEY` and `OPENAI_MODEL`.
- Anthropic: set `ANTHROPIC_API_KEY` and `ANTHROPIC_MODEL`.
- Disabled: deterministic fallback only.

AI output is treated as untrusted input, parsed and validated against a Pydantic schema. Never execute suggested fixes automatically.

## Main API

- `GET /health/live` — process liveness
- `GET /health/ready` — database readiness
- `POST /api/v1/auth/register` — create an account
- `POST /api/v1/auth/login` — OAuth2-compatible token login
- `GET /api/v1/auth/me` — current user
- `POST /api/v1/reviews` — review code (authenticated)
- `GET /api/v1/reviews` — current user's recent review history
- `GET /api/v1/reviews/{review_id}` — one review
- `POST /api/v1/github/webhook` — verify GitHub webhook signature; PR event processing is intentionally a documented extension point

## Example request

```json
{
  "language": "python",
  "code": "import os\npassword = 'admin123'\nprint(password)"
}
```

## Testing and quality

```bash
cd backend
pytest
ruff check app tests
bandit -r app
```

## Important hardening before production

- Set strong unique `SECRET_KEY` and `GITHUB_WEBHOOK_SECRET`; do not commit `.env`.
- Put the app behind HTTPS and a reverse proxy with request-size/rate limits.
- Configure allowed frontend origins with `CORS_ORIGINS`.
- Use managed secrets, DB backups, monitoring, alerting, and log retention policies.
- Add GitHub App installation-token flow and PR diff retrieval before claiming full PR reviews; webhook signature verification alone is not PR integration.
- Configure Alembic migrations for controlled schema upgrades.

## Validation status

CI is configured to run backend linting, Bandit, backend tests, frontend TypeScript/build checks, Docker Compose configuration validation, and image builds. A green CI run is required before claiming the project is production-ready.

## Container publishing

The `docker-publish.yml` workflow publishes backend and frontend images to GitHub Container Registry (GHCR) when code is pushed to `main`, a `v*` tag is pushed, or the workflow is run manually. The repository must allow GitHub Actions to write packages. Review workflow permissions and image visibility in repository settings after the first run.

This workflow publishes container images; it does not deploy them to a live server. Configure a separate deployment target and protected environment if automated production deployment is required.
