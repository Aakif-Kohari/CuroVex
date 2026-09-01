# CuroVex — Database Schema

CuroVex uses two databases with different jobs: **Neo4j** holds the biomedical knowledge
graph itself (the thing being reasoned over), and **PostgreSQL** holds application state
(the thing the product runs on). They are never merged — this keeps the graph reusable and
the app state simple.

## 1. Neo4j graph schema

### Node labels

| Label | Key properties | Source |
|---|---|---|
| `Drug` | `id`, `name`, `drugbank_id`, `atc_code` | PrimeKG / DRKG |
| `Disease` | `id`, `name`, `mondo_id`, `category` | PrimeKG |
| `Gene` | `id`, `symbol`, `entrez_id` | PrimeKG |
| `Protein` | `id`, `uniprot_id`, `name` | PrimeKG |
| `Pathway` | `id`, `name`, `reactome_id` | PrimeKG |
| `SideEffect` | `id`, `name`, `meddra_id` | PrimeKG |

### Relationship types

| Type | From → To | Properties |
|---|---|---|
| `TREATS` | `Drug → Disease` | `source`, `confidence` |
| `TARGETS` | `Drug → Protein` | `mechanism`, `affinity` |
| `ASSOCIATED_WITH` | `Gene → Disease` | `evidence_score` |
| `PART_OF_PATHWAY` | `Gene/Protein → Pathway` | — |
| `CAUSES_SIDE_EFFECT` | `Drug → SideEffect` | `frequency` |
| `INTERACTS_WITH` | `Protein → Protein` | `interaction_type` |
| `PREDICTED_TREATS` | `Drug → Disease` | `score`, `model_version`, `generated_at` — **written by CuroVex, not sourced from PrimeKG** |

`PREDICTED_TREATS` is the output relationship the model writes back into the graph, kept
distinct from the ground-truth `TREATS` edges so provenance is always clear.

## 2. PostgreSQL application schema

```mermaid
erDiagram
    USERS ||--o{ SAVED_SEARCHES : creates
    USERS ||--o{ PREDICTION_RUNS : requests
    PREDICTION_RUNS ||--o{ PREDICTIONS : produces
    PREDICTIONS ||--o{ EXPLANATIONS : has
    PREDICTIONS ||--o{ VALIDATION_RESULTS : has

    USERS {
        uuid id PK
        string email
        string password_hash
        timestamp created_at
    }
    SAVED_SEARCHES {
        uuid id PK
        uuid user_id FK
        string disease_query
        timestamp created_at
    }
    PREDICTION_RUNS {
        uuid id PK
        uuid user_id FK
        string disease_id
        string model_version
        timestamp started_at
        timestamp completed_at
    }
    PREDICTIONS {
        uuid id PK
        uuid run_id FK
        string drug_id
        string drug_name
        string disease_id
        float score
        int rank
    }
    EXPLANATIONS {
        uuid id PK
        uuid prediction_id FK
        string method
        float fidelity_score
        jsonb subgraph
    }
    VALIDATION_RESULTS {
        uuid id PK
        uuid prediction_id FK
        boolean has_clinical_trial
        boolean has_literature_support
        string evidence_url
    }
```

### Notes
- `EXPLANATIONS.method` is either `path_based` or `counterfactual` — the same prediction can
  have both, which is what makes the comparison study (XAI-3/XAI-4 in the backlog) possible.
- `EXPLANATIONS.subgraph` stores the explanation subgraph as JSON (node/edge IDs) so the
  frontend can re-render it without re-querying Neo4j on every page load.
- No patient data, no PII beyond account email — this schema was deliberately kept clear of
  anything that would need an ethics board.
