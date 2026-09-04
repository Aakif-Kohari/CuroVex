# CuroVex

<p align="center">
  <em>Explainable AI framework for drug repurposing using biomedical knowledge graphs and counterfactual reasoning.</em>
</p>

**Status:** Phases 1 & 2 implemented — testing and deployment in progress — BE Computer Science (Data Science) Final Year Major Project, 2026–2027

---

## 🔬 What is CuroVex?

Finding new uses for existing, FDA-approved drugs (drug repurposing) drastically cuts down research and development time. **CuroVex** is an end-to-end Machine Learning pipeline and web platform that predicts new therapeutic uses for these existing drugs by reasoning over a massive public biomedical knowledge graph.

Unlike other black-box AI tools, CuroVex explains *why* it made each prediction using two methodologies:
1. **Path-Based Explanations (Baseline):** Highlights the graph connections bridging a drug and a disease.
2. **Counterfactual Edge-Masking (Novel Contribution):** Systematically removes edges from the explanation subgraph and checks if the prediction breaks. By generating a **fidelity score**, CuroVex *proves* its reasoning holds up under scrutiny—an approach previously unexplored in this domain.

---

## 🛠️ Tech Stack & Architecture

Our system is composed of six distinct layers:

- **Knowledge Graph:** Neo4j (populated via PrimeKG / DRKG)
- **Machine Learning Core:** PyTorch Geometric (GAT Link Prediction), PyKEEN (Embeddings: TransE, RotatE, ComplEx, DistMult)
- **Backend API:** FastAPI, Postgres (SQLAlchemy / Alembic), Celery + Redis (Asynchronous Tasks)
- **Explainability Engine:** Path-based + Novel Counterfactual Masking Modules
- **Validation Engine:** Automated cross-referencing via ClinicalTrials.gov and PubMed APIs
- **Frontend Dashboard:** Next.js 14, TailwindCSS, Cytoscape.js (Graph Visualization)

> **Deep Dive:** Read the comprehensive [System Architecture](docs/SYSTEM_ARCHITECTURE.md) and [Database Schema](docs/DATABASE_SCHEMA.md) documentation.

---

## 🚀 Features

- **End-to-End Prediction:** Query a disease and receive a ranked list of candidate drugs in real-time.
- **Dual Explainability:** View side-by-side comparisons of path-based meta-paths and counterfactual edge-masking fidelity scores.
- **Interactive Graph UI:** Visualize the drug-disease relationships with our interactive Cytoscape dashboard.
- **Automated Validation:** Automatically flags whether a predicted pair is actively being studied in ClinicalTrials.gov or mentioned in recent PubMed literature.
- **Save & Share:** JWT-authenticated user sessions for saving searches and prediction runs.

---

## 📖 Documentation Directory

| Document | Description |
|---|---|
| [System Architecture](docs/SYSTEM_ARCHITECTURE.md) | High-level overview of layers, tech stack, and data flow. |
| [Product Backlog](docs/PRODUCT_BACKLOG.md) | Epics, user stories, and feature tracking. |
| [Database Schema](docs/DATABASE_SCHEMA.md) | Neo4j graph schema and relational Postgres models. |
| [Roadmap](ROADMAP.md) | Our two-semester execution plan. |
| [Kanban Workflow](docs/KANBAN.md) | GitHub Projects board rules and sprint rhythm. |
| [Deployment Guide](docs/DEPLOYMENT_CHECKLIST.md) | Instructions for deploying the stack on free-tier cloud providers. |
| [Contributing Guide](CONTRIBUTING.md) | Setup instructions for local development and branch rules. |

*(Note: Formal submission documents including the Project Charter, Product Vision, SRS, and Test Plan are submitted separately as faculty deliverables).*

---

## 💻 Getting Started (Local Development)

To spin up the entire CuroVex ecosystem on your local machine:

### 1. Clone the repository
```bash
git clone https://github.com/Aakif-Kohari/CuroVex.git
cd CuroVex
```

### 2. Environment Configuration
```bash
cp .env.example .env
# Edit .env with any necessary overrides (e.g., SECRET_KEY, NEO4J credentials)
```

### 3. Spin up the Database & Redis via Docker
```bash
docker compose up -d postgres redis neo4j
```

### 4. Run the Pipeline & API
```bash
# Setup Python environment
python -m venv .venv
source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
pip install -r requirements.txt

# Apply Postgres Migrations
cd api
alembic upgrade head
cd ..

# Run Celery Worker (In a separate terminal)
celery -A api.celery_app worker --loglevel=info

# Run FastAPI Backend
uvicorn api.main:app --reload
```

### 5. Start the Frontend Dashboard
```bash
cd dashboard
pnpm install
pnpm dev
```

Visit `http://localhost:3000` to interact with the CuroVex dashboard!

---

## 👥 Meet the Team

- **Aakif Kohari** - [GitHub](https://github.com/Aakif-Kohari)
- **Usaid Duldule** - [GitHub](https://github.com/Usaid582000)
- **Tabeer Ansari** - [GitHub](https://github.com/Ansari-Tabeer)
- **Mohd Nooh Rais** - [GitHub](https://github.com/RAISnooh09)

---

## 📄 License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for more information.
