# CuroVex — Kanban Board Setup

Use **GitHub Projects** (Projects tab → New project → Board layout), not a separate tool —
keeps issues, PRs, and the board in one place with zero sync overhead.

## Columns

| Column | Meaning | WIP limit |
|---|---|---|
| **Backlog** | Not started, not yet prioritized into a sprint | — |
| **To Do** | Prioritized for the current phase (see Roadmap) | — |
| **In Progress** | Actively being worked | 2 per person |
| **In Review** | PR open, awaiting review/CI | — |
| **Done** | Merged to `dev` or `main` | — |

## Card = one backlog item

Every card title starts with its backlog ID from `docs/PRODUCT_BACKLOG.md`, e.g.
`XAI-2: Counterfactual edge-masking with fidelity score`. Create a GitHub Issue per card so
it links to PRs automatically.

## Labels

| Label | Use |
|---|---|
| `epic:kg` `epic:ml` `epic:xai` `epic:validation` `epic:api` `epic:frontend` `epic:devops` `epic:docs` | matches backlog epics |
| `priority:P0` `priority:P1` `priority:P2` | matches backlog priority |
| `blocked` | dependency not ready |
| `good-first-issue` | onboarding-friendly tasks |

## Definition of done

A card only moves to **Done** when:
1. Code merged to `dev` (or `main` for release-tagged work)
2. Tests written and passing in CI
3. Docs updated if the change affects setup, API surface, or schema
4. No `TODO`/`FIXME` left unaddressed without a linked follow-up issue

## Sprint rhythm

- Weekly planning: move items from Backlog → To Do based on the current Roadmap phase.
- Mid-week check-in: anything stuck In Progress > 4 days gets flagged in team chat.
- Friday: move finished cards to Done, retro on anything blocked.
