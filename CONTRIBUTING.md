# Contributing to CuroVex

Onboarding guide for the four-person team. Follow this once when you first clone the repo.

## 1. Prerequisites

- Docker Desktop (or Docker Engine + Compose plugin)
- Python 3.11+
- Node.js 20+ and pnpm (`npm i -g pnpm`)
- Git

## 2. First-time setup

```bash
git clone https://github.com/Aakif-Kohari/CuroVex.git
cd CuroVex
cp .env.example .env          # fill in local secrets — never commit .env
docker compose up -d          # starts Neo4j, Postgres, Redis
```

Backend:
```bash
cd api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt --break-system-packages
uvicorn main:app --reload
```

Frontend:
```bash
cd dashboard
pnpm install
pnpm dev
```

Verify: API docs at `http://localhost:8000/docs`, dashboard at `http://localhost:3000`,
Neo4j browser at `http://localhost:7474`.

## 3. Branch strategy

- `main` — protected, always deployable. No direct pushes.
- `dev` — integration branch. Feature branches merge here first.
- `feature/<epic-id>-<short-desc>` — e.g. `feature/xai-2-counterfactual-masking`

## 4. Commit conventions

Conventional Commits, kept short:
```
feat(explainability): add edge-masking fidelity scorer
fix(api): correct pagination on /predictions endpoint
docs: update database schema for validation_results table
```

## 5. Pull request process

1. Open PR against `dev`, link the backlog ID (e.g. `Closes XAI-2`).
2. At least 1 teammate approval required before merge.
3. CI (lint + tests) must pass — no merging red builds.
4. Squash-merge; delete branch after merge.

## 6. Code style

- Python: `black` + `ruff`, type hints required on public functions.
- TypeScript: `eslint` + `prettier`, strict mode on.
- No `console.log` / `print` debugging left in merged code — use `structlog` / proper
  logging.

## 7. Team

| Name | GitHub | Suggested focus area |
|---|---|---|
| Aakif Kohari | [@Aakif-Kohari](https://github.com/Aakif-Kohari) | ML / embeddings, GAT, explainability engine |
| Usaid Duldule | [@Usaid582000](https://github.com/Usaid582000) | Backend — FastAPI, Celery, Postgres |
| Tabeer Ansari | [@Ansari-Tabeer](https://github.com/Ansari-Tabeer) | Frontend — Next.js dashboard, graph visualization |
| Mohd Nooh Rais | [@RAISnooh09](https://github.com/RAISnooh09) | Data / DevOps — KG ingestion, CI/CD, deployment |

Adjust these once the team confirms who's owning what — they're suggested splits based on
the four architecture layers, not fixed assignments.

## 8. Where things live

See [`docs/SYSTEM_ARCHITECTURE.md`](docs/SYSTEM_ARCHITECTURE.md) for the full layer
breakdown and repo folder structure, and [`docs/PRODUCT_BACKLOG.md`](docs/PRODUCT_BACKLOG.md)
for what to work on next.
