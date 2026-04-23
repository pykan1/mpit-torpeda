# Driveery — NL2SQL Analytics Platform

> **Hackathon project** — MPIT III season, Specialists track  
> Case sponsor: **Drivee** ride-sharing platform

## What is Driveery?

"ChatGPT for your database" — manager types natural language, system returns SQL + chart + AI thinking log.

```
Manager: "Топ-3 города по отменённым поездкам за неделю"
   ↓ AI generates SQL
   ↓ Guardrails check (no DROP/DELETE/sensitive data)
   ↓ Execute on Drivee database
   ↓ Auto-select chart type (bar/line/pie)
   ↓ Show AI "chain of thought" to user
```

## Quick Start (Local)

### Backend
```bash
cd backend
pip3 install -r requirements.txt
# Edit .env if needed (default uses SQLite)
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**

### With Docker
```bash
docker compose up -d
```
(Start Docker Desktop first)

## Architecture

```
backend/app/
  domain/           → Entities, exceptions (pure Python)
  application/      → Use cases: nl2sql_service, security_service, chart_service
  infrastructure/   → SQLAlchemy models, OpenRouter AI client
  api/v1/           → FastAPI routers, Pydantic schemas
```

## Database Schema (8 tables)

| Table | Description |
|-------|-------------|
| `users` | Platform users with roles (admin/analyst/manager/viewer) |
| `cities` | Drivee operating cities |
| `drivers` | Driver profiles with ratings |
| `trips` | Core metric — 800 seeded records |
| `orders` | Order records by channel |
| `saved_reports` | Saved NL queries with scheduling |
| `query_logs` | Full audit log with AI thinking |
| `semantic_terms` | Business terms dictionary |

## Key Features

- **NL2SQL** — Qwen3.6-plus via OpenRouter with thinking mode
- **AI Thinking Logs** — full chain-of-thought visible to user
- **Guardrails** — blocks DROP/DELETE/sensitive columns
- **Auto Charts** — bar/line/pie/KPI selection, toggle to table
- **Semantic Layer** — business terms → SQL mapping
- **Saved Reports** — with scheduling (daily/weekly)
- **Security Panel** — role management, SQL validator, audit

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/query` | NL → SQL → execute → chart |
| GET | `/api/v1/templates` | Quick-start query templates |
| GET/POST | `/api/v1/reports` | Saved reports |
| GET | `/api/v1/logs` | AI query audit log |
| GET | `/api/v1/stats` | Platform statistics |
| GET/POST | `/api/v1/semantic` | Business terms dictionary |
| GET/PATCH | `/api/v1/users` | User management |
| POST | `/api/v1/validate-sql` | SQL guardrail test |

Swagger UI: **http://localhost:8000/docs**

## Tech Stack

- **Frontend**: Vue 3, Pinia, Tailwind CSS (Drivee brand colors), Chart.js
- **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.x async, Pydantic v2
- **AI**: OpenRouter API, `qwen/qwen3.6-plus` (thinking mode)
- **DB**: SQLite (dev) / PostgreSQL (prod via Docker)
- **DevOps**: Docker, Docker Compose
