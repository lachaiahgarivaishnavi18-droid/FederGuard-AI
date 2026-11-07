# FederGuard AI

A privacy-conscious, synthetic research prototype for cross-bank fraud intelligence. A working React/FastAPI application, three independent local bank processes, model training, federated aggregation, privacy accounting, permission-filtered retrieval, analyst workflows, and reproducible evaluations.

**Hosted research demo:** [federguard-ai.vercel.app](https://federguard-ai.vercel.app). The API and three bank services run as separate Vercel Python projects with isolated Neon roles/schemas. See [the cloud architecture](docs/neon-vercel.md). Cloud signup uses only email and password; local user accounts are not automatically migrated to the cloud database. The seeded demo accounts use the configured `DEMO_PASSWORD`.

**All records are synthetic.** This is decision support. No account freezing, payment blocking, reporting of people, or legally binding decisions are implemented. The bank network is a local simulation, not independently operated institutional infrastructure. Aggregation is explicitly plaintext; it is not cryptographic secure aggregation. See [limitations](docs/limitations.md) before interpreting privacy or ML results.

## Start locally

Use **Python 3.12** and **Node 22+**. Python 3.15 is not the supported dependency target. From the repository root in PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe -m scripts.dev init
.\.venv\Scripts\python.exe -m scripts.dev all
```

In another terminal:

```powershell
cd frontend
corepack enable
corepack prepare pnpm@10.28.2 --activate
pnpm install --frozen-lockfile
pnpm dev
```

Open **http://localhost:5173**. Use `bank_a@federguard.demo`, `bank_b@federguard.demo`, or `bank_c@federguard.demo`. The generated `DEMO_PASSWORD` is in your ignored `.env`; it is never committed. Bank A has the demo administrator role. Banks B/C have reviewer roles. Sign in as Bank A to start a federated round. View the honest early-round evaluation, score a synthetic feature vector, create an investigation, add notes, ask the assistant for evidence, and inspect the graph.

To register, click **Create account** and enter only your email and password. In demo mode, registration creates a separate analyst workspace automatically. No institution selection, invitation code or password confirmation is required. Joining an existing institution through the API still requires its invitation; open registration is disabled outside demo mode.

Bank credentials are independently generated. Each bank process receives only its own credential in Docker. Local launching uses a shared host and administrative `.env` for convenience, which is **not institutional secret isolation**.

Linux/macOS: use `python3.12 -m venv .venv` and `.venv/bin/python` in place of the Windows Python path.

### Start services individually

Each command runs in a separate terminal at the repository root:

```powershell
.\.venv\Scripts\python.exe -m scripts.dev backend
.\.venv\Scripts\python.exe -m scripts.dev bank_a
.\.venv\Scripts\python.exe -m scripts.dev bank_b
.\.venv\Scripts\python.exe -m scripts.dev bank_c
```

Coordinator/API: `127.0.0.1:8000`; bank nodes: `8101`, `8102`, `8103`. The frontend development proxy keeps browser API calls on the same origin. Use `localhost:5173`, matching `FRONTEND_ORIGIN`; a different hostname is rejected for state changes until configured.

### Native Flower transport

The web coordinator dispatches authenticated local training requests and uses Flower's FedAvg aggregation engine. A second runner exercises native Flower gRPC scheduling and independent `NumPyClient` processes:

```powershell
# Set a NEW unique FLOWER_RUN_ID for each experiment in every terminal.
$env:FLOWER_RUN_ID='my-unique-experiment-001'
.\.venv\Scripts\python.exe -m backend.federated.flower server --rounds 3
# Separate terminals, with the same FLOWER_RUN_ID:
.\.venv\Scripts\python.exe -m backend.federated.flower bank_a
.\.venv\Scripts\python.exe -m backend.federated.flower bank_b
.\.venv\Scripts\python.exe -m backend.federated.flower bank_c
```

Native transport logs public synthetic evaluation to `runtime/flower-evaluation.jsonl`; it does not populate the web registry. This compatibility runner uses Flower's legacy server/client APIs. It defaults to loopback and does not authenticate institution membership. TLS can be configured with `FLOWER_TLS_CA`, `FLOWER_TLS_CERT`, `FLOWER_TLS_KEY` and `FLOWER_ADDRESS`. Do not expose it to an untrusted network. It does not enable SecAgg+.

## Commands

```powershell
# Start actual federated training through the running coordinator
.\.venv\Scripts\python.exe -m scripts.api round

# Train/evaluate local and centralized models, federated models and privacy noise settings
.\.venv\Scripts\python.exe -m scripts.evaluate --rounds 5

# Ingest a document into Bank A's private knowledge base
.\.venv\Scripts\python.exe -m scripts.api ingest --file data/sample_policies/velocity.md
.\.venv\Scripts\python.exe -m scripts.api query --text "Explain suspicious transaction velocity"
.\.venv\Scripts\python.exe -m scripts.api agents --text "Explain account takeover indicators"

# Labeled synthetic retrieval benchmark (running API required)
.\.venv\Scripts\python.exe -m scripts.evaluate_rag

# API, isolation, privacy, aggregation and workflow tests
.\.venv\Scripts\python.exe -m pytest -q
# Three-process native Flower smoke check
.\.venv\Scripts\python.exe -m scripts.flower_check

# Frontend types and production bundle
cd frontend
pnpm build
```

The browser QA script is `scripts/browser-check.cjs`. Install Playwright separately (`pnpm add -D playwright` in a test environment and `playwright install chromium`), or set `PLAYWRIGHT_MODULE` to an existing module and optionally `CHROMIUM_PATH`. Run it at the repository root with the frontend/backend/nodes running. It verifies all 13 authenticated routes, cited answers, local scoring, case creation, and desktop/mobile overflow. Screenshots are in `docs/screenshots`.

## Implemented capabilities

| Area | Behavior |
| --- | --- |
| Identity | Scrypt password hashes, expiring opaque HttpOnly sessions, logout revocation, origin checks, login limits, invitation-based analyst registration, institution-scoped reviewer creation through `POST /api/users` |
| Data locality | 4,500 / 3,500 / 2,000 non-IID synthetic rows in separate bank stores, missing values, imbalance, synthetic drift in Bank C; no coordinator transaction table or dataset mounting |
| Local ML | Fixed public preprocessing, logistic risk ranking, exact additive feature contributions; five synthetic-only baseline models and SHAP evaluation artifacts |
| Federation | Authenticated HTTP dispatch, Flower FedAvg, optional FedProx local regularization, version registry, public cohort weights, failed clients, dropout scenario, quorum checks, anomalous tensor rejection, public holdout metrics |
| Privacy | Per-record gradient clipping, Gaussian gradients, supported Opacus RDP accountant, sequential release composition, local budget enforcement, replay caching, no re-enabling DP after an unprotected local release |
| Intelligence | Bank consent, minimized structured contribution, evidence links, confidence, expiry, private/consortium permissions, separate human reviewer approval |
| Retrieval | PDF/DOCX/TXT/MD parsing, bounded uploads, overlapping chunks, provenance, BM25 + TF-IDF fallback, configurable SentenceTransformers/FAISS and cross-encoder, permission filtering before ranking/generation |
| AI | Extractive local demo, OpenAI-compatible/local, Anthropic and Gemini provider adapters, evidence citations, citation ID validation, insufficient-evidence response, downloadable text report |
| Graph | Permission-filtered NetworkX graph, evidence relationships, degree centrality, analytical communities, interactive React Flow display |
| Agents | 13 typed LangGraph stages with scoped outputs, dependency errors, bounded retries and provenance audit; local training is a separate explicit operation |
| Investigations | Tenant-scoped cases, model references, notes, assignment on creation, evidence links, reviewer-controlled outcomes and review history |
| Operations | Responsive dashboard, privacy center, measured analytics, audit trail, WebSocket round endpoint, Docker/Compose, TLS ingress example, health endpoint, Alembic starter |

## Database and files

SQLite is the local default: `runtime/coordinator.db`. Bank-local training journals and synthetic arrays are under `runtime/bank_a`, `runtime/bank_b`, and `runtime/bank_c`. Only bank processes load those arrays. The central database has identity/membership, sessions, banks, client participation and typed resource records for models, rounds, evidence, intelligence, cases, queries, agents and audit. It deliberately does **not** create unused placeholder tables for every proposed domain entity. Further normalization is a documented remaining integration.

PostgreSQL is selected using `DATABASE_URL=postgresql+psycopg://user:password@host/federguard`. Install requirements before using it. SQLAlchemy creates the initial local schema at startup. Alembic migration entry point:

```powershell
.\.venv\Scripts\python.exe -m alembic -c backend/alembic.ini upgrade head
```

Run migrations before deploying schema changes; do not rely on `create_all` to upgrade existing tables. The initial migration and PostgreSQL deployment are supplied but Docker/PostgreSQL were not executed in this environment.

## Configuration

The source template is `.env.example`. `scripts.dev init` generates local secrets without printing them. To create a second reviewer, sign in as a bank administrator and call `POST /api/users` with `{email,password,role:"reviewer"}`. A contribution's author cannot approve their own contribution. A new institution's endpoint and secret must be configured in its own `<BANK_ID>_ENDPOINT` and `<BANK_ID>_CLIENT_KEY` environment variables before enrollment.

External generation: set `LLM_PROVIDER` to `openai`, `anthropic`, `gemini`, or `local`, plus `LLM_MODEL`, `LLM_API_KEY` where required, and `LLM_BASE_URL` for compatible/local servers. Credentials are never browser-side. Configuring an external provider authorizes egress of the retrieved, permitted evidence to that provider; validate institutional policy first. No external provider was tested with live credentials.

Neural retrieval: configure `SEMANTIC_MODEL` with an installed/downloadable SentenceTransformers model and optional `RERANKER_MODEL` cross-encoder. With no model configured, the UI explicitly identifies BM25 + TF-IDF fallback. Neural models are not downloaded automatically during initial launch. Indexes currently rebuild from authorized evidence in memory per request; durable vector indexing is a remaining integration.

## Deployment

Set a unique `POSTGRES_PASSWORD` in `.env`, then `docker compose up --build`. Open `http://localhost:8080`. Compose mounts separate persistent bank volumes, separate internal bank networks, and no bank datasets into the coordinator. Plain HTTP is only a local demonstration. For institutional deployment configure TLS for ingress **and each bank link**, secure cookies, private networking, managed secrets, encrypted volumes/backups, authenticated enrollment, and independent review. See [deployment](docs/deployment.md).

## Project layout

```text
frontend/                 React + Vite + TypeScript + Tailwind
  src/pages/              Fifteen separate page modules
  src/shared.tsx          Shared UI, session context, data hook and formatting
  src/                    Application shell, UI styles, API client
backend/
  app/                    API, security/persistence, schemas, orchestration, RAG
  federated/              Native Flower transport and Dockerfile
  ml.py                   Public preprocessing, model metrics, Flower FedAvg
  migrations/             Initial Alembic schema
  tests/                  API, locality, isolation, privacy, federation tests
bank_clients/             Isolated node app, local datasets/models/accounting
scripts/                  Setup, process launcher, CLI, evaluations, browser QA
data/sample_policies/     Synthetic input document
docs/
  architecture.md         System and training flow diagrams
  privacy.md              Mechanism and accounting assumptions
  threat-model.md         Controls and residual risks
  deployment.md           Operating/backup runbook
  limitations.md          Explicit scope and remaining integrations
  reports/                Measured ML, privacy utility, SHAP, retrieval reports
  screenshots/            Desktop/mobile browser verification artifacts
deployment/               Nginx and TLS ingress examples
docker-compose.yml        PostgreSQL + coordinator + three bank nodes + UI
```

API documentation is generated at `http://127.0.0.1:8000/docs` and `/openapi.json`. [API guide](docs/api.md) documents workflows and permissions. [Validation record](docs/validation.md) records what was and was not exercised.
