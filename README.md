# CyberGuard AI

Standalone, full-stack **AI-assisted cybersecurity monitoring** platform: FastAPI + PostgreSQL + Redis + Celery backend, Next.js (App Router) frontend, rule-based detection, optional OpenRouter AI, PDF reports, and WebSocket alert broadcasts.

## Prerequisites

- Docker and Docker Compose **or** local Python 3.12+, Node 20+, PostgreSQL 16+, Redis 7+
- Optional: [OpenRouter](https://openrouter.ai/) API key for AI incident analysis

## Quick start (Docker)

From the repository root:

```bash
cp backend/.env.example backend/.env
# Set SECRET_KEY and optionally OPENROUTER_API_KEY in backend/.env or export in shell

docker compose up --build
```

**OpenRouter in Docker:** Put `OPENROUTER_API_KEY=...` in **`backend/.env`**. Compose injects that file into the `api` and `worker` services. Do **not** rely only on `OPENROUTER_API_KEY` in a repo-root `.env` unless you also export it in your shell—previously an empty override could hide the key from the container.

- API: `http://localhost:8000` — docs at `http://localhost:8000/docs`
- **Migrations:** The API container runs `alembic upgrade head` on startup (before Uvicorn). You do not need a separate `exec` step for a normal `docker compose up`.

Create a user via the UI at `http://localhost:3000/signup` (with the frontend running locally, see below) or use the API `POST /api/v1/auth/signup`.

### Demo data

With API running and `DATABASE_URL` set (e.g. inside the API container):

```bash
docker compose exec api python scripts/seed_demo.py
```

Or from the app UI: **Settings → Full SOC demo scenario** (scripted alerts: brute force, port scan, denied spike, login burst, rate anomaly) or **Random synthetic batch**.

## Frontend (local dev)

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Open `http://localhost:3000`. Set `NEXT_PUBLIC_API_URL` in `.env.local` if the API is not on `http://127.0.0.1:8000`.

**Landing hero video (optional):** Place `hero.mp4` and optional `hero-poster.jpg` in [`frontend/public/`](frontend/public/). If `hero.mp4` exists, the marketing hero uses it as a subtle background; otherwise the animated gradient is used.

## Backend (local, without Docker API container)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp .env.example .env
# Start PostgreSQL and Redis, then:
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Celery worker (optional, for async AI/PDF tasks):

```bash
celery -A app.tasks.celery_app:celery_app worker --loglevel=INFO
```

Celery Beat (optional, for scheduled digest reports):

```bash
celery -A app.tasks.celery_app:celery_app beat --loglevel=INFO
```

## Architecture

- **REST API** under `/api/v1` — JWT auth (`Authorization: Bearer`), pagination via `page` / `page_size`
- **WebSocket** — `WS /api/v1/ws?token=<access_jwt>` — pushes JSON when new alerts are created
- **Detection** — Modular rules (failed logins, brute force, port scan, denied spike, rate anomaly); high/critical alerts open incidents
- **AI** — `POST /api/v1/incidents/{id}/analyze` (sync or `async_task=true` with Celery); requires `OPENROUTER_API_KEY` on the server
- **Reports** — `POST /api/v1/incidents/{id}/generate-report` queues PDF generation (styled PDF with charts); download via `GET /api/v1/reports/{id}/download`
- **Scheduled digests** — `GET/POST/PATCH/DELETE /api/v1/report-schedules` (per user). **Celery Beat** runs every 15 minutes and emails a digest PDF when `SMTP_HOST` and `SMTP_FROM` are set; otherwise the PDF is still written to `REPORTS_DIR`. Configure schedules in **Settings** in the app.

## AI Detection Copilot

CyberGuard AI uses a hybrid detection model. Deterministic rules remain the official source of alerts and severity, while the AI Detection Copilot runs asynchronously after event ingestion to classify attack type, explain evidence, suggest severity, map MITRE context, and recommend response actions.

The AI copilot is intentionally a second opinion, not an uncontrolled replacement for rules. If OpenRouter is not configured, event ingestion, rule detections, alerts, incidents, dashboards, and reports continue to work normally.

### AI detection flow

1. A user ingests events through the API, upload flow, synthetic data, or Cyber Range.
2. `EventService` stores the events and runs deterministic rules immediately.
3. After commit, the backend queues a Celery AI classification task for the new event IDs.
4. The AI classifier sends structured event context to OpenRouter and asks for compact JSON only.
5. The result is stored in `ai_classifications` and returned as `ai_assessment` on event and alert responses.
6. A separate `ai_classifier` alert is created only for high-confidence suspicious classifications when no rule alert already exists.
7. AI suggested severity never overwrites the official rule alert severity automatically.

### AI classification output

| Field | Meaning |
|---|---|
| `attack_type` | Normalized class such as `brute_force`, `sql_injection`, `path_traversal`, `port_scan`, `data_exfiltration`, `ransomware`, `benign`, or `unknown`. |
| `confidence` | Model confidence from `0.0` to `1.0`. |
| `suggested_severity` | AI recommendation only; official severity remains rule-based unless an analyst changes it. |
| `why_classified` | Short explanation grounded in the observed event fields. |
| `evidence` | Concrete indicators cited from the event or raw log. |
| `mitre_tactics` / `mitre_techniques` | AI-suggested MITRE context for analyst review. |
| `recommended_actions` | Practical next steps for triage and response. |
| `should_create_alert` | AI recommendation used with server-side confidence and evidence guardrails. |

### AI detection APIs

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v1/events/{event_id}/ai-classification` | Return the AI classification for one event. |
| `GET` | `/api/v1/alerts/{alert_id}/ai-classification` | Return the AI classification linked to an alert or its triggering event. |

### AI detection environment variables

| Variable | Default | Purpose |
|---|---|---|
| `AI_DETECTION_ENABLED` | `true` | Enables async AI event classification. |
| `AI_DETECTION_MIN_CONFIDENCE` | `0.85` | Minimum confidence required before AI can create an AI-only alert. |
| `AI_DETECTION_MAX_EVENTS_PER_TASK` | `20` | Maximum events classified by one Celery task. |
| `OPENROUTER_API_KEY` | empty | Required for AI classification and incident AI analysis. |
| `OPENROUTER_MODEL` | `openai/gpt-4o-mini` | Model used for AI copilot prompts. |

### Defense explanation

The correct academic explanation is: rules provide deterministic, testable detection, and AI provides analyst-style interpretation. This is safer than AI-only detection because false positives and model mistakes do not silently change official severity. It is more useful than report-only AI because the model participates earlier in the SOC workflow and explains attack type directly from event evidence.

## Controlled Cyber Range

CyberGuard AI includes a local-only Cyber Range mode inside the Attack Lab. It lets an examiner launch realistic attack patterns against a deliberately vulnerable mini target container while keeping all activity inside Docker and localhost.

The range target is not a production service. It contains dummy users, dummy files, and disposable in-memory state so that brute-force, SQL injection, path traversal, exfiltration, ransomware-behavior, and port-scan demonstrations can create real HTTP/TCP telemetry without touching real systems or host files.

### Safety model

- The vulnerable target is the `range-target` Docker service and is published only as `127.0.0.1:8088:8088`.
- The backend runner uses only hardcoded scenario IDs and the configured `RANGE_TARGET_URL`; it rejects targets outside the local allowlist.
- No user-supplied external URL is accepted by the range APIs.
- The target container has no host filesystem mounts and uses disposable container state plus `tmpfs`.
- Management endpoints for log collection and reset require `RANGE_SHARED_SECRET`.
- CLI examples in the UI are local-only `curl` commands for `http://127.0.0.1:8088`.

### Range APIs

All range APIs require normal CyberGuard authentication.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v1/range/status` | Check whether the local range target is enabled and healthy. |
| `GET` | `/api/v1/range/scenarios` | List approved local range scenarios, expected detections, MITRE mappings, safety notes, and CLI examples. |
| `POST` | `/api/v1/range/scenarios/{scenario_id}/run` | Execute one approved scenario against the local range target and ingest collected logs as CyberGuard events. |
| `POST` | `/api/v1/range/collect` | Import logs generated manually from local CLI/curl demonstrations. |
| `POST` | `/api/v1/range/reset` | Reset only the vulnerable target dummy state and drain range logs; it does not delete CyberGuard users or SOC data. |

### Range environment variables

| Variable | Default | Purpose |
|---|---|---|
| `RANGE_ENABLED` | `true` | Enables or disables the Cyber Range API. |
| `RANGE_TARGET_URL` | `http://range-target:8088` | Internal Docker URL used by the backend runner. |
| `RANGE_PUBLIC_URL` | `http://127.0.0.1:8088` | Local URL shown to the examiner for browser/curl demonstrations. |
| `RANGE_SHARED_SECRET` | `dev-range-secret-change-me` | Development-only shared token for target reset and log drain endpoints. Change it for demos. |

### Doctor demo flow

1. Start the stack with `docker compose up --build`.
2. Open the frontend and log in.
3. Go to **Attack Lab**.
4. Select **Cyber Range**.
5. Launch a scenario such as **Local SQL Injection Attempt**.
6. Open Events, Alerts, Incidents, Dashboard, or Reports to see telemetry and detections.
7. Optionally run one of the local CLI examples shown on a scenario card, then click **Collect Range Logs**.
8. Click **Reset Range** before repeating a demonstration.

### Phase 1 range scenarios

| Scenario | Target | Expected detections |
|---|---|---|
| Local Brute Force Login | `POST /login` | `brute_force`, `failed_login_burst` |
| Local SQL Injection Attempt | `GET /search?q=...` | `sql_injection_attempt` |
| Local Path Traversal Attempt | `GET /files?path=...` | `path_traversal_attempt` |
| Local Data Exfiltration Simulation | `POST /exfil` | `data_exfiltration` |
| Local Ransomware Behavior Simulation | `POST /ransomware/simulate` | `ransomware_simulation` |
| Controlled Local Port Scan | approved ports `8088-8103` on the range container | `port_scan` |

## Security notes

- JWT secrets must be strong in production (`SECRET_KEY`).
- Access tokens are stored in `localStorage` in this demo UI; prefer httpOnly cookies and a BFF for production hardening.
- CORS is configured via `CORS_ORIGINS` in `backend/.env`.

## Project layout

- `backend/` — FastAPI app (`app/`), Alembic, Docker image
- `frontend/` — Next.js App Router, shadcn/ui, TanStack Query, Zustand, Recharts, Framer Motion
- `docker-compose.yml` — Postgres, Redis, API, Celery worker, Celery Beat

## SMTP (scheduled digest email)

Optional variables in `backend/.env` (see `backend/.env.example`):

- `SMTP_HOST`, `SMTP_PORT` (default `587`), `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_USE_TLS` (default `true`)

Use **Send test email** on **Settings** after configuring. Without SMTP, digests are generated on disk only.

## Docker troubleshooting

- **`exec format error` for `uvicorn` / `celery`:** Usually a **CPU architecture mismatch** (e.g. ARM vs x86). This repo sets **`platform: linux/amd64`** on the API, worker, and beat services and uses `python -m uvicorn` / `python -m celery`. Rebuild without cache:  
  `docker compose build --no-cache api worker beat && docker compose up`
- If you need **native ARM** images instead, remove the `platform:` lines from `docker-compose.yml` for those services, then rebuild.
- **Stale image / old `passlib` / bcrypt errors in the container:** After changing `backend/` code or `requirements.txt`, rebuild so the running image matches:  
  `docker compose build --no-cache api worker beat && docker compose up`
- **`alembic upgrade` → `DuplicateTable` (e.g. `users` already exists):** The database was created earlier while Alembic’s `alembic_version` table was empty or out of sync. **If the API container is still running** (bash / macOS / Linux shell):  
  `docker compose exec api alembic stamp 001`  
  `docker compose exec api alembic upgrade head`  
  On **Windows PowerShell**, run the same two commands one at a time (PowerShell 5.x does not support `&&` between host commands).  
  **If the API keeps crashing on startup**, run Alembic **inside** the container (not on the Windows host — `/app` exists only in the image). Prefer calling **`alembic` as the entrypoint** (avoids `sh -c`, which Docker Desktop on Windows sometimes breaks — you may see `cannot open -c`):  
  `docker compose run --rm --entrypoint alembic api stamp 001`  
  `docker compose run --rm --entrypoint alembic api upgrade head`  
  **Interactive fallback (any OS):** `docker compose run --rm -it --entrypoint sh api` then run `cd /app && alembic stamp 001 && alembic upgrade head` in that shell.  
  Then `docker compose up`. If you can wipe dev data, `docker compose down -v` and `docker compose up --build` creates a clean database from migrations alone.

## QA / demo scenarios

| # | Scenario | What to do | Expected |
|---|----------|------------|----------|
| 1 | Onboarding | Sign up → log in → dashboard | Session works, KPIs load |
| 2 | Brute force | Synthetic events or ingest many failed auths from one IP in a few minutes | Alert + incident |
| 3 | Port scan | Ingest ≥15 **distinct** `port` values from the **same** `source_ip` within **2 minutes** (`event_type=network`) | “Possible port scan” with **Ports:** list in summary; Port column on incident events |
| 4 | AI analysis | Incident → **Run AI analysis** (with `OPENROUTER_API_KEY`) | Summary/remediation update; loading animation while pending |
| 5 | Incident PDF | **Generate PDF report** → Reports → download | Styled PDF with chart + events table |
| 6 | Digest schedule | Settings → add schedule; wait for Beat (≤15 min) or inspect `REPORTS_DIR` | PDF `digest_u*.pdf`; email if SMTP set |
| 7 | Fresh stack | `docker compose down -v` → `up --build` | Migrations apply; empty DB |

## License

MIT (align with your organization’s policy).
