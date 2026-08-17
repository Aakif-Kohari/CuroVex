# CuroVex — Roadmap

Two-semester plan for a four-person team. Dates are indicative sprint targets, not hard
deadlines — adjust against your actual academic calendar.

## Semester 7 — Foundation & core pipeline

| Phase | Weeks | Goal | Backlog epics |
|---|---|---|---|
| Phase 1 — Setup | 1–2 | Repo, Docker Compose stack, CI skeleton running | Epic 7 |
| Phase 2 — Knowledge graph | 3–6 | PrimeKG ingested into Neo4j, DRKG cross-check working | Epic 1 |
| Phase 3 — Prediction model | 7–11 | Embeddings benchmarked, GAT trained, candidate ranking works end-to-end | Epic 2 |
| Phase 4 — Baseline explainability | 12–14 | Path-based explanation generation working | Epic 3 (XAI-1) |
| Milestone review | 15 | Demo: search disease → ranked drugs → path explanation | — |

**Sem 7 deliverable:** working prediction pipeline with baseline (path-based) explanations,
Project Charter, SRS, System Architecture doc submitted.

## Semester 8 — Novelty, product, and release

| Phase | Weeks | Goal | Backlog epics |
|---|---|---|---|
| Phase 5 — Counterfactual engine | 1–4 | Edge-masking + fidelity scoring implemented and benchmarked against baseline | Epic 3 (XAI-2 to XAI-4) |
| Phase 6 — Validation layer | 5–6 | ClinicalTrials.gov / PubMed cross-reference automated | Epic 4 |
| Phase 7 — API + auth | 5–8 | FastAPI endpoints complete, Celery jobs, Postgres wired up | Epic 5 |
| Phase 8 — Frontend | 7–11 | Dashboard with interactive graph explanation view | Epic 6 |
| Phase 9 — Deploy & harden | 12–13 | Free-tier deployment live, CI/CD building images | Epic 7 |
| Phase 10 — Paper & report | 12–15 | Fidelity/sparsity comparison written up as the research contribution | — |
| Final review | 16 | Full demo + paper submission + final report | — |

**Sem 8 deliverable:** deployed, publicly reachable product; research paper on the
counterfactual explainability comparison; final report and documentation set.

## Non-negotiable checkpoints
- End of Sem 7: prediction pipeline must run end-to-end on a real disease query — this is
  the point most similar student projects stall, so treat it as the hard gate.
- Mid Sem 8: counterfactual engine must produce a fidelity score that's demonstrably
  different from the path-based baseline on the same prediction — this is the entire
  novelty claim, so don't leave it until the last phase.
