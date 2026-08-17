# CuroVex — Deployment Checklist

Deploy target: free-tier services only, no institutional approval required.

| Service | Platform | Notes |
|---|---|---|
| Graph DB | Neo4j Aura Free | 1 instance, ~200k node limit — fine for a scoped PrimeKG subset |
| API | Render or Railway free tier | Dockerized FastAPI + Celery worker |
| Task queue broker | Redis (Render/Railway managed free tier) | |
| App DB | Render/Railway managed Postgres free tier | |
| Frontend | Vercel | Next.js, zero-config deploy from `main` |

## Pre-deploy checklist

- [ ] All CI checks green on `main`
- [ ] `.env.example` reflects every required environment variable (no secrets committed)
- [ ] Neo4j Aura instance provisioned, connection string in secrets
- [ ] Postgres migrations applied (`alembic upgrade head`)
- [ ] Model artifact (TorchScript export) uploaded to the deploy target, path configured
- [ ] CORS origins in FastAPI updated to the production frontend URL
- [ ] Sentry DSN configured for both API and frontend
- [ ] Rate limiting enabled on public endpoints

## Deploy steps

1. Tag release: `git tag vX.Y.Z && git push --tags`
2. GitHub Actions builds and pushes Docker images (see `.github/workflows/ci.yml`)
3. Deploy API service on Render/Railway, point at the new image tag
4. Run Postgres migrations against production DB
5. Deploy frontend on Vercel (auto-triggers on push to `main`)
6. Verify Neo4j Aura connection from the deployed API (`/health` endpoint)

## Post-deploy smoke test

- [ ] `GET /health` returns 200
- [ ] `GET /predictions/{known_disease_id}` returns a non-empty ranked list
- [ ] `GET /explanations/{prediction_id}` returns both `path_based` and `counterfactual`
      explanations
- [ ] Dashboard loads, search works, graph visualization renders
- [ ] Error tracking (Sentry) receives a test event

## Rollback plan

- Keep the previous Docker image tag deployed alongside the new one until smoke tests pass.
- If smoke tests fail: redeploy previous image tag on Render/Railway, revert Vercel to
  previous deployment (one click in Vercel dashboard), do not roll back Postgres migrations
  unless the new migration is confirmed broken.
