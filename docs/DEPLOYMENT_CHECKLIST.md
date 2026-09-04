# CuroVex — Deployment Checklist

**Deploy target:** Modern free-tier / low-cost cloud services. No institutional approval required.

## 🏗 Architecture Overview

| Service | Platform | Notes |
|---|---|---|
| Graph DB | Neo4j Aura Free | ~200k node / 400k relationship cap — graph is subsetted (excludes `INTERACTS_WITH`, `CAUSES_SIDE_EFFECT`) via `--exclude-rel-types` in `kg-etl.yml` to stay under the relationship cap |
| App DB | Neon Free | Render's free Postgres expires after 30–90 days; Neon persists |
| API | Render Free (Docker image from GHCR) | Image built + pushed by `.github/workflows/ci.yml`'s `build-and-push` job; Render deploys the `ghcr.io/aakif-kohari/curovex/api:latest` image directly rather than building from source |
| Model artifacts | GitHub Release asset | Produced by `.github/workflows/train-model.yml`; downloaded at container boot by `api/start.sh` via `ARTIFACTS_URL` |
| Frontend | Vercel | Next.js, zero-config deploy from `main` |

*Note: Sentry error tracking, API rate limiting, and Celery/Redis are scaffolded but no endpoint currently calls `.delay()` — safe to skip deploying for now.*

## Pre-deploy checklist

- [ ] All CI checks green on `main`, including `build-and-push`
- [ ] `kg-etl.yml` run against the Aura instance, confirmed relationship count < 400k
- [ ] `train-model.yml` run, artifacts tarball uploaded as a GitHub Release, `ARTIFACTS_URL` copied
- [ ] `.env.example` reflects every required variable (no secrets committed)
- [ ] Neon connection string set as `DATABASE_URL` on Render
- [ ] `NEO4J_URI` / `NEO4J_USER` / `NEO4J_PASSWORD` set on Render (Aura uses `neo4j+s://`)
- [ ] `ARTIFACTS_URL` set on Render
- [ ] CORS origins on Render updated to the deployed Vercel URL
- [ ] `NEXT_PUBLIC_API_URL` set on Vercel to the Render URL

## Deploy steps

1. Push to `main` — CI builds and pushes `ghcr.io/aakif-kohari/curovex/api:latest`
2. On Render: point the web service at that GHCR image (Existing Image deploy, not a repo build)
3. Render boot: `start.sh` downloads artifacts, runs `alembic upgrade head`, starts `uvicorn`
4. Deploy frontend on Vercel (auto-triggers on push to `main`)
5. Set `CORS_ORIGINS` on Render to the real Vercel URL, redeploy

## Post-deploy smoke test

- [ ] `GET /health` returns 200
- [ ] `GET /predictions/{a disease id present in the subsetted graph}` returns a non-empty ranked list
- [ ] `GET /explanations/{prediction_id}` returns both `path_based` and `counterfactual`
- [ ] Dashboard loads, search works, graph visualization renders
- [ ] No CORS errors in browser devtools

## Rollback plan

- Render: redeploy the previous image tag/digest from the service's deploy history
- Vercel: revert to the previous deployment (one click)
- Don't roll back Postgres migrations unless the new migration is confirmed broken
