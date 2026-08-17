# CuroVex

> Explainable AI framework for drug repurposing using biomedical knowledge graphs and counterfactual reasoning.

**Status:** In active development — BE Computer Science (Data Science) Final Year Major Project, 2026–2027

## What is CuroVex

CuroVex predicts new therapeutic uses for existing drugs by reasoning over a public
biomedical knowledge graph, then explains *why* it made each prediction two ways: a
conventional path-based explanation, and a **counterfactual edge-masking** explanation
that tests whether the explanation actually holds up by removing the evidence and
checking whether the prediction breaks. No prior system in this space tests its own
explanations this way — see [`docs/SYSTEM_ARCHITECTURE.md`](docs/SYSTEM_ARCHITECTURE.md)
for the full novelty case.

## Architecture

Six layers: public knowledge graphs → Neo4j → KG embedding + GAT link prediction →
explainability engine (path-based + counterfactual) → FastAPI backend → Next.js dashboard.

Full breakdown: [`docs/SYSTEM_ARCHITECTURE.md`](docs/SYSTEM_ARCHITECTURE.md)

## Documentation

| Doc | Purpose |
|---|---|
| [System Architecture](docs/SYSTEM_ARCHITECTURE.md) | Layers, tech stack, data flow |
| [Product Backlog](docs/PRODUCT_BACKLOG.md) | Epics, user stories, priorities |
| [Database Schema](docs/DATABASE_SCHEMA.md) | Neo4j graph schema + Postgres schema |
| [Roadmap](ROADMAP.md) | Two-semester phase plan |
| [Kanban setup](docs/KANBAN.md) | GitHub Projects board structure |
| [Deployment checklist](docs/DEPLOYMENT_CHECKLIST.md) | Free-tier deploy steps |
| [Contributing](CONTRIBUTING.md) | Dev environment setup, branch/PR rules |

Formal submission documents (Project Charter, Product Vision, SRS, Test Plan) are kept
outside the repo as faculty deliverables.

## Getting started

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the full setup guide. Quick version:

```bash
git clone https://github.com/Aakif-Kohari/CuroVex.git
cd CuroVex
cp .env.example .env
docker compose up -d
```

## Repository structure

```
curovex/
├── kg-pipeline/      # ETL: PrimeKG/DRKG ingestion → Neo4j
├── ml-core/          # PyKEEN embeddings, GAT model, training scripts
├── explainability/   # path-based + counterfactual masking modules
├── validation/       # ClinicalTrials.gov / PubMed cross-reference scripts
├── api/              # FastAPI app, Celery tasks, Postgres models
├── dashboard/        # Next.js frontend
├── docs/             # architecture, backlog, schema, roadmap, etc.
└── .github/workflows/  # CI/CD
```

## Team

- [Aakif Kohari](https://github.com/Aakif-Kohari)
- [Usaid Duldule](https://github.com/Usaid582000)
- [Tabeer Ansari](https://github.com/Ansari-Tabeer)
- [Mohd Nooh Rais](https://github.com/RAISnooh09)

## License

Apache License 2.0 — see [LICENSE](LICENSE).
