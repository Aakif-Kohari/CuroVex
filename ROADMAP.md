# CuroVex — Roadmap

Check items off as they land. Work top to bottom within a phase — most items depend on the
one before it.

## Phase 1 — Foundation & Core Pipeline

Goal: a disease query returns a ranked drug list with a working baseline explanation.
Nothing after this phase works until this phase works.

- [ ] 1.1 — Confirm local dev environment: clone repo, `docker compose up -d`, verify Neo4j (localhost:7474), Postgres, and Redis are all reachable.
- [ ] 1.2 — Write `kg-pipeline/download_primekg.py`: downloads PrimeKG source files and saves them locally.
- [ ] 1.3 — Write `kg-pipeline/normalize_schema.py`: maps PrimeKG's raw columns onto the node/relationship schema defined in `docs/DATABASE_SCHEMA.md`.
- [ ] 1.4 — Write `kg-pipeline/load_to_neo4j.py`: loads the normalized data into Neo4j via the Neo4j Python driver, idempotently (safe to re-run).
- [ ] 1.5 — Write `kg-pipeline/crosscheck_drkg.py`: downloads DRKG and compares entity/relation counts against the loaded PrimeKG graph, prints a discrepancy report.
- [ ] 1.6 — Write `ml-core/benchmark_embeddings.py`: uses PyKEEN to train and score TransE, RotatE, ComplEx, DistMult on the graph; logs results to MLflow; prints the best model by AUPRC.
- [ ] 1.7 — Write `ml-core/train_gat.py`: trains a PyTorch Geometric GAT link-prediction model on top of the best embedding from 1.6.
- [ ] 1.8 — Write `ml-core/predict.py`: given a `disease_id`, returns a ranked list of candidate drugs with scores.
- [ ] 1.9 — Write `explainability/path_based.py`: given a `(drug_id, disease_id)` pair, returns the meta-path(s) connecting them in the graph.
- [ ] 1.10 — Write unit tests for 1.4, 1.6, 1.8, 1.9 (`pytest`, in each module's own test file).
- [ ] 1.11 — Milestone check: manually run disease query → ranked drugs → path explanation end-to-end on 2–3 known diseases; sanity-check the output makes sense.

**Phase 1 exit criteria:** the pipeline runs end to end from the command line. No API, no
frontend yet — that's Phase 2.

## Phase 2 — Novelty Engine, Product & Release

Goal: the counterfactual explainability engine (the actual research contribution) is built
and benchmarked, then wrapped in a working, deployed product.

- [ ] 2.1 — Write `explainability/counterfactual.py`: masks one graph edge at a time from a prediction's local subgraph, re-runs the model, records the score change.
- [ ] 2.2 — Add fidelity scoring to 2.1: quantify how much each masked edge mattered.
- [ ] 2.3 — Write `explainability/compare_methods.py`: runs both path-based and counterfactual explanations on a shared test set of predictions, outputs a fidelity/sparsity comparison table.
- [ ] 2.4 — Write `validation/clinicaltrials_check.py`: queries the ClinicalTrials.gov API for a given drug–disease pair, returns whether a trial exists.
- [ ] 2.5 — Write `validation/pubmed_check.py`: queries PubMed E-utilities for recent literature mentioning a given drug–disease pair.
- [ ] 2.6 — Scaffold `api/`: FastAPI app structure (`main.py`, `models.py`, `routers/`), Pydantic schemas matching `docs/DATABASE_SCHEMA.md`.
- [ ] 2.7 — Implement `GET /predictions/{disease_id}` (wraps 1.8).
- [ ] 2.8 — Implement `GET /explanations/{prediction_id}` (wraps 1.9 and 2.1, returns both methods).
- [ ] 2.9 — Implement `GET /validation/{prediction_id}` (wraps 2.4 and 2.5).
- [ ] 2.10 — Set up Postgres models + Alembic migrations for `users`, `saved_searches`, `prediction_runs`, `predictions`, `explanations`, `validation_results`.
- [ ] 2.11 — Add Celery task queue for long-running batch prediction jobs.
- [ ] 2.12 — Add JWT auth: `POST /auth/register`, `POST /auth/login`.
- [ ] 2.13 — Scaffold `dashboard/`: Next.js app, base layout, API client.
- [ ] 2.14 — Build disease search screen + ranked results list.
- [ ] 2.15 — Build explanation detail screen: Cytoscape.js subgraph view, toggle between path-based and counterfactual.
- [ ] 2.16 — Build validation evidence display (trial/literature badges) on the results screen.
- [ ] 2.17 — Deploy: Neo4j Aura Free, API on Render/Railway, frontend on Vercel — following `docs/DEPLOYMENT_CHECKLIST.md`.
- [ ] 2.18 — Run the post-deploy smoke test checklist from `docs/DEPLOYMENT_CHECKLIST.md`.
- [ ] 2.19 — Write up the fidelity/sparsity comparison from 2.3 as the paper's results section.
- [ ] 2.20 — Final report, documentation pass, demo rehearsal.

**Phase 2 exit criteria:** publicly reachable URL, both explanation methods visible and
compared, paper draft complete.
