# CuroVex — Product Backlog

Organized by epic, mapped to the six architecture layers. Priority: **P0** (must-have for a
working demo), **P1** (needed for the "production-ready" bar), **P2** (stretch / polish).

## Epic 1 — Knowledge graph construction & ingestion
| ID | User story | Priority |
|---|---|---|
| KG-1 | As a developer, I can run one script to download and normalize PrimeKG into a common schema | P0 |
| KG-2 | As a developer, I can load the normalized graph into Neo4j with a single command | P0 |
| KG-3 | As a developer, I can cross-check node/relation counts against DRKG for validation | P1 |
| KG-4 | As a developer, I can version and diff graph snapshots across runs | P1 |
| KG-5 | As a developer, I can incrementally update the graph without a full reload | P2 |

## Epic 2 — KG embedding & link prediction
| ID | User story | Priority |
|---|---|---|
| ML-1 | As a researcher, I can benchmark TransE/RotatE/ComplEx/DistMult via PyKEEN and log results to MLflow | P0 |
| ML-2 | As a researcher, I can train a GAT link-prediction model on top of the best embedding | P0 |
| ML-3 | As a researcher, I can generate a ranked list of candidate drug–disease pairs for any disease node | P0 |
| ML-4 | As a developer, I can export the trained model for fast inference in the API | P1 |
| ML-5 | As a researcher, I can retrain on an updated graph snapshot without changing downstream code | P2 |

## Epic 3 — Explainability engine
| ID | User story | Priority |
|---|---|---|
| XAI-1 | As a researcher, I can generate meta-path explanations for a given prediction (baseline) | P0 |
| XAI-2 | As a researcher, I can run counterfactual edge-masking on a prediction and get a fidelity score | P0 |
| XAI-3 | As a researcher, I can compare path-based vs. counterfactual explanations on the same prediction | P1 |
| XAI-4 | As a researcher, I can benchmark fidelity and sparsity across both methods on a test set | P1 |
| XAI-5 | As a user, I can see a plain-language summary of why a drug was recommended | P2 |

## Epic 4 — Validation & evidence layer
| ID | User story | Priority |
|---|---|---|
| VAL-1 | As a researcher, I can check whether a predicted drug–disease pair has a registered clinical trial | P0 |
| VAL-2 | As a researcher, I can check whether recent PubMed literature mentions a predicted pair | P1 |
| VAL-3 | As a user, I can see a "supporting evidence" badge on predictions with external validation | P1 |

## Epic 5 — Backend API
| ID | User story | Priority |
|---|---|---|
| API-1 | As a frontend, I can request predictions for a disease via `GET /predictions/{disease_id}` | P0 |
| API-2 | As a frontend, I can request an explanation for a prediction via `GET /explanations/{prediction_id}` | P0 |
| API-3 | As a user, I can register/log in and my searches are saved | P1 |
| API-4 | As a developer, long-running jobs (batch predictions) run via Celery and don't block requests | P1 |
| API-5 | As a developer, all endpoints are documented via auto-generated OpenAPI/Swagger | P1 |

## Epic 6 — Frontend dashboard
| ID | User story | Priority |
|---|---|---|
| UI-1 | As a user, I can search for a disease and see ranked drug candidates | P0 |
| UI-2 | As a user, I can click a candidate and see its explanation subgraph visually | P0 |
| UI-3 | As a user, I can toggle between path-based and counterfactual explanation views | P1 |
| UI-4 | As a user, I can see validation evidence (trials/literature) alongside a prediction | P1 |
| UI-5 | As a user, I can save and revisit past searches | P2 |

## Epic 7 — DevOps & deployment
| ID | User story | Priority |
|---|---|---|
| OPS-1 | As a developer, I can spin up the full stack locally with `docker compose up` | P0 |
| OPS-2 | As a developer, CI runs lint + tests on every PR | P0 |
| OPS-3 | As a developer, merges to `main` build and push Docker images | P1 |
| OPS-4 | As a team, the demo is deployed and publicly reachable (free tiers) | P1 |

## Epic 8 — Documentation & testing
| ID | User story | Priority |
|---|---|---|
| DOC-1 | As a new contributor, I can follow the onboarding guide to get a working dev environment | P0 |
| DOC-2 | As a reviewer, I can read the SRS and architecture doc to understand scope | P0 |
| DOC-3 | As a developer, unit tests cover the embedding, GAT, and counterfactual modules | P1 |
| DOC-4 | As a developer, integration tests cover the API endpoints end-to-end | P1 |
