# CuroVex — Deployment Checklist

**Deploy target:** Modern free-tier / low-cost cloud services. No institutional approval required.

## 🏗 Architecture Overview

| Service | Platform | Notes |
|---|---|---|
| **Graph DB** | Neo4j Aura Free | 1 instance. *Note: 400k relationship cap. `kg-pipeline` must subset PrimeKG to fit.* |
| **API & Celery** | Render | Dockerized FastAPI (Web Service) + Celery (Background Worker). |
| **Container Registry** | GitHub Container Registry (GHCR) | Images pushed via GitHub Actions to `ghcr.io/aakif-kohari/curovex/...` |
| **Task Broker** | Redis | Render managed Redis (or Upstash free tier). |
| **App DB (Postgres)**| Neon.tech | **Do not use Render Postgres** (it expires/deletes after 30-90 days). Neon provides a permanent free tier. |
| **Frontend** | Vercel | Next.js 14. **Must configure build command to use `pnpm`**. |
| **Model Artifacts** | GitHub Releases / S3 | Standard PyTorch state dicts (`.pt`), *not* TorchScript. Downloaded on cold-start via `start.sh`. |

---

## ✅ Pre-deploy Checklist

### 1. Databases & Infrastructure
- [ ] **Neon Postgres**: Provision project, get connection string (Transaction pooler mode recommended for serverless/Render).
- [ ] **Neo4j Aura**: Provision free instance, get `NEO4J_URI`, `NEO4J_USER`, and `NEO4J_PASSWORD`.
- [ ] **Redis**: Provision Render Redis or Upstash.

### 2. GitHub Secrets (Repository Settings > Secrets and variables > Actions)
- [ ] `DATABASE_URL` (Neon connection string)
- [ ] `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
- [ ] `REDIS_URL`
- [ ] `SECRET_KEY` (Randomly generated string for JWT signing)
- [ ] `ARTIFACTS_URL` (URL to your GitHub Release or S3 bucket hosting the `.pt` model weights)

### 3. Codebase Readiness
- [ ] All CI checks green on `main` (Linting, Pytest, Jest, Docker Build).
- [ ] `.env.example` reflects every required environment variable (no secrets committed).
- [ ] CORS origins in `api/main.py` updated to include the production Vercel URL.
- [ ] `api/start.sh` is executable and correctly configured to download weights from `ARTIFACTS_URL`.

---

## 🚀 Deploy Steps

### Step 1: Trigger the CI/CD Pipeline
1. Ensure all code is merged to `main`.
2. The GitHub Actions workflow (`.github/workflows/ci.yml`) will automatically:
   - Run all backend/frontend tests.
   - Build the Docker images.
   - Push the API and Dashboard images to **GHCR** (`ghcr.io/aakif-kohari/curovex/api:latest`).

### Step 2: Deploy Backend (Render)
1. Create a new **Web Service** on Render.
2. Connect your GitHub repository.
3. **Root Directory**: `api` (or use the Dockerfile path `api/Dockerfile` depending on Render's Docker setup).
4. **Environment Variables**: Add all secrets from the Pre-deploy checklist.
5. Deploy.
6. Create a **Background Worker** on Render using the same image/repo, pointing the start command to your Celery worker.

### Step 3: Apply Database Migrations
1. Open the Render Web Service shell or run locally against the production Neon DB:
   ```bash
   alembic upgrade head
   ```

### Step 4: Deploy Frontend (Vercel)
1. Import the GitHub repository into Vercel.
2. **Root Directory**: `dashboard`
3. **Framework Preset**: Next.js
4. **Build Command**: `pnpm build`
5. **Install Command**: `pnpm install`
6. **Environment Variables**: Add `NEXT_PUBLIC_API_URL` (pointing to your Render API URL).
7. Deploy (will auto-deploy on future pushes to `main`).

---

## 🧪 Post-deploy Smoke Test

- [ ] **API Health**: `GET /health` returns `200 OK` and confirms DB/Neo4j connectivity.
- [ ] **Predictions**: `GET /predictions/{known_disease_id}` returns a non-empty ranked list.
- [ ] **Explanations**: `GET /explanations/{prediction_id}` returns both `path_based` and `counterfactual` payloads.
- [ ] **Frontend**: Dashboard loads, search works, and the Cytoscape graph visualization renders without CORS errors.
- [ ] **Model Download**: Check Render logs to ensure `start.sh` successfully downloaded the `.pt` weights from `ARTIFACTS_URL` on cold start.

---

## ⏪ Rollback Plan

- **API/Worker**: Render keeps previous Docker deployments. If the new image crashes, click "Rollback" in the Render deployments tab to the previous successful GHCR digest.
- **Frontend**: Vercel maintains a history of deployments. Click "Promote to Production" on the previous successful deployment in the Vercel dashboard.
- **Database**: **Do not roll back Postgres migrations** unless the new schema change is confirmed broken and data-loss is acceptable. If a migration breaks, write a *new* migration to reverse the changes.
