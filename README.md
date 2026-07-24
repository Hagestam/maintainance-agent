# RT Knits Maintenance Agent

AI-powered maintenance coordination system for RT Knits, built for the **CBBR-NATEC Innovation Cup 2026**.

Factory workers report issues over **WhatsApp**. An AI agent triages each request, creates prioritized work orders, and coordinates technicians through a lightweight CMMS backend. Nightly jobs generate preventive maintenance work and dispatch daily plans.

---

## Features

- **AI maintenance triage** — Claude classifies priority (P0 / P1 / P2), asks only when critical details are missing, and creates work orders
- **WhatsApp integration** — inbound messages and photos via `whatsapp-web.js`; outbound alerts via a local Express bridge
- **Automated technician assignment** — finds available techs and builds nightly dispatch plans
- **Preventive maintenance scheduling** — materializes PM work orders and assigns open P1/P2 jobs (max 6 per tech)
- **Emergency P0 interrupt** — bumps a tech’s lowest-priority job and sends a WhatsApp alert
- **Feedback / reward gate** — quality checks to reduce “cobra effect” (speed-only gaming)
- **Dashboard APIs** — list work orders, technicians, assets, and stats
- **Photo attachments** — images saved under `uploads/work_order_photos/`

---

## Architecture

```
WhatsApp (phone)
       │
       ▼
 bridge.js  (whatsapp-web.js + Express :3000)
       │  POST /api/chat
       ▼
 FastAPI  (app/main.py :8000)
       │
       ▼
 agents/orchestrator.py  →  Claude + tools
       │
       ├── tools/cmms_tools.py      (create WO, search assets, find tech, history)
       ├── tools/admin_tools.py     (view / delete WOs — admin numbers only)
       ├── tools/whatsapp_tools.py  (outbound → bridge :3000/send-message)
       ├── tools/pm_planner.py      (generate PM work orders)
       ├── tools/planning_tools.py  (nightly plan + dispatch)
       ├── tools/dispatch_tools.py  (P0 emergency assign)
       └── tools/reward_tools.py    (feedback scoring)
       │
       ▼
 PostgreSQL  (SQLAlchemy models)
```

**Nightly scheduler** (APScheduler): every day at **18:00**, runs `build_nightly_plan` (PM generation + assignments + WhatsApp dispatch).

---

## Tech stack

| Layer | Technology |
|--------|------------|
| API | Python, FastAPI, Uvicorn |
| Config | pydantic-settings, python-dotenv |
| Database | PostgreSQL, SQLAlchemy 2 |
| AI | Anthropic Claude (`claude-haiku-4-5`) |
| WhatsApp | Node.js, Express, whatsapp-web.js, qrcode-terminal |
| Scheduling | APScheduler |
| Seed data | openpyxl (Excel data pack) |

---

## Prerequisites

- **Python 3.10+** (3.12+ recommended)
- **Node.js 18+** and npm
- **PostgreSQL** running locally or remotely
- **Anthropic API key**
- **Chrome / Chromium** (Puppeteer for WhatsApp Web; bridge runs with `headless: false` by default)

---

## Quick start

### 1. Clone and enter the repo

```bash
git clone https://github.com/Hagestam/maintainance-agent.git
cd maintainance-agent
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your real values (see [Environment variables](#environment-variables)).

### 3. Create the database

```bash
# Example with psql
createdb maintainance_agent
# Or via SQL:
# CREATE DATABASE maintainance_agent;
```

Ensure `DATABASE_URL` in `.env` points at that database.

### 4. Python setup

```bash
python3 -m venv env
source env/bin/activate          # Windows: env\Scripts\activate
pip install -r requirements.txt
```

### 5. Create tables

```bash
python -m database.init_db
```

You should see: `All tables created.`

### 6. Seed sample CMMS data (optional but recommended)

Requires the Excel files under `RTknits CMMS Data Pack/RTknits CMMS Data Pack/`:

```bash
python seed_data.py
```

Seeds departments, assets, technicians, tasks, and work orders from:

- `users_department.xlsx`
- `Assets.xlsx`
- `Technicians.xlsx`
- `Tasks.xlsx`
- `Workorder.xlsx`

### 7. Node (WhatsApp bridge)

```bash
npm install
```

### 8. Run both services

**Terminal 1 — FastAPI**

```bash
source env/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: http://localhost:8000  
- Swagger UI: http://localhost:8000/docs  
- Health: http://localhost:8000/health  

**Terminal 2 — WhatsApp bridge**

```bash
node bridge.js
```

- Bridge HTTP: http://localhost:3000 (`POST /send-message`)
- Scan the QR code in the terminal with WhatsApp (Linked devices)
- Session is stored in `.wwebjs_auth/`

Keep both processes running. Inbound WhatsApp messages go to FastAPI; outbound agent/dispatch messages go through the bridge.

---

## Environment variables

All settings are loaded from a `.env` file in the project root (`app/config.py`).  
**Every field below is required at startup** — missing values will prevent the app from booting.

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | SQLAlchemy Postgres URL, e.g. `postgresql://user:pass@localhost:5432/maintainance_agent` |
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key used by the orchestrator |
| `WHATSAPP_TOKEN` | Yes* | Placeholder for legacy Meta Cloud API config |
| `PHONE_NUMBER_ID` | Yes* | Placeholder for legacy Meta Cloud API config |
| `WHATSAPP_VERIFY_TOKEN` | Yes* | Placeholder for legacy Meta webhook verify |

\*These three are declared in `Settings` and must be present, but the **current** WhatsApp path uses `bridge.js` (WhatsApp Web), not the Meta Cloud API. Use the placeholders from `.env.example` unless you wire Cloud API yourself.

### Example `.env`

```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/maintainance_agent
ANTHROPIC_API_KEY=sk-ant-your-key-here
WHATSAPP_TOKEN=unused
PHONE_NUMBER_ID=unused
WHATSAPP_VERIFY_TOKEN=unused
```

### Not env-driven (hardcoded today)

| Setting | Location | Notes |
|---------|----------|--------|
| Bridge send URL | `tools/whatsapp_tools.py` | `http://localhost:3000/send-message` |
| FastAPI chat URL | `bridge.js` | `http://localhost:8000/api/chat` |
| Ports | bridge / uvicorn | `3000` / `8000` |
| Admin WhatsApp IDs | `tools/admin_tools.py` → `ADMIN_NUMBERS` | Edit the list to grant admin WO tools |
| Claude model | `agents/orchestrator.py` | `claude-haiku-4-5` |
| Nightly plan time | `tools/scheduler.py` | Cron `18:00` daily |
| Photo upload dir | `tools/image_store.py` | `uploads/work_order_photos/` |

---

## Priority model

Derived by the agent from the requester’s description (`prompts/intake_prompt.txt`):

| Priority | Meaning |
|----------|---------|
| **P0** | Production stopped, or safety hazard |
| **P1** | Employee wellbeing (heat, lighting, ergonomics) — not production-stopping |
| **P2** | Everything else (cosmetic, non-urgent, improvements) |

Work order types include `PREVENTIVE`, `PLANNED`, and `REACTIVE`.

---

## API reference

Interactive docs: **http://localhost:8000/docs**

### Core

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/chat` | Chat / agent entry (used by the WhatsApp bridge) |

**Chat body**

```json
{
  "user": "2547XXXXXXXX@c.us",
  "message": "Machine 12 is overheating and line is stopped",
  "image_base64": null,
  "image_mime_type": null
}
```

**Response**

```json
{ "reply": "Work order created..." }
```

### Dashboard (`/api`)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/workorders` | List WOs (optional `status`, `priority` query params) |
| `GET` | `/api/technicians` | List technicians |
| `GET` | `/api/assets` | List assets |
| `GET` | `/api/stats` | Totals by priority + open jobs |
| `POST` | `/api/trigger-planning` | Run nightly plan immediately |

### Manual test harness (`/test`)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/test/1-generate-pms` | Generate PM work orders for tomorrow |
| `POST` | `/test/3-p0-interrupt` | Assign emergency P0 (`p0_wo_id`, `tech_id`) |
| `POST` | `/test/4-feedback-gate` | Feedback / reward gate (`wo_id`, `rating`) |

### Bridge (Node)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `http://localhost:3000/send-message` | Send WhatsApp message `{ "phone", "message" }` |

---

## Project structure

```
maintainance-agent/
├── app/
│   ├── main.py                 # FastAPI app, lifespan scheduler, chat + test routes
│   └── config.py               # Settings from .env
├── agents/
│   └── orchestrator.py         # Claude tool-calling agent (active)
├── api/routes/
│   ├── whatsapp_webhook.py     # Chat webhook router
│   └── dashboard.py            # REST read APIs
├── models/                     # SQLAlchemy models
├── database/
│   ├── database.py             # Engine + SessionLocal
│   ├── base.py
│   └── init_db.py              # create_all tables
├── tools/                      # CMMS, WhatsApp, PM, dispatch, rewards, scheduler
├── prompts/
│   └── intake_prompt.txt       # System prompt for the orchestrator
├── bridge.js                   # WhatsApp Web + Express bridge
├── seed_data.py                # Excel → Postgres seeder
├── requirements.txt
├── package.json
├── .env.example
├── uploads/work_order_photos/  # Stored request photos
└── RTknits CMMS Data Pack/     # Challenge data + docs
```

---

## Typical usage flow

1. Start FastAPI and `bridge.js`, then link WhatsApp via QR.
2. A worker sends a message (and optional photo) describing a fault.
3. Bridge posts to `/api/chat`; the orchestrator may call tools (`create_work_order`, `search_assets`, etc.).
4. Reply is sent back on WhatsApp.
5. At 18:00 (or via `/api/trigger-planning`), the system builds the next-day plan and notifies technicians.
6. Admins (numbers in `ADMIN_NUMBERS`) can view or delete work orders through the agent.

---

## Troubleshooting

| Issue | What to check |
|-------|----------------|
| App fails on import / `ValidationError` for Settings | `.env` missing or incomplete — copy `.env.example` and fill all keys |
| DB connection errors | Postgres running; `DATABASE_URL` user/password/db name correct |
| `anthropic` / `openpyxl` import errors | `pip install -r requirements.txt` inside the activated venv |
| Bridge cannot reach API | FastAPI must be on port **8000** before messages arrive |
| Outbound WhatsApp fails | Bridge must be on port **3000** and authenticated |
| QR / Puppeteer issues | Install Chromium/Chrome; on servers you may need `headless: true` and extra Chromium args in `bridge.js` |
| Admin tools denied | Add your WhatsApp ID to `ADMIN_NUMBERS` in `tools/admin_tools.py` |
| Seed path errors | Confirm Excel files live at `RTknits CMMS Data Pack/RTknits CMMS Data Pack/` |

---

## Notes

- There is no Docker Compose or Alembic migration pipeline yet — schema is created with `python -m database.init_db`.
- WhatsApp sessions (`.wwebjs_auth/`, `.wwebjs_cache/`) and `.env` should stay local; do not commit secrets.
- Production hardening would typically include env-based bridge/API URLs, headless Chromium, and a hosted WhatsApp channel instead of a desktop Web session.

---

## License

ISC — see `package.json`.
