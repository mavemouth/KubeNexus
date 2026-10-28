# KuberNexus — Developer Handoff Guide

> **Kubernetes Resource Optimization Platform**  
> SE Project · SEM 5 · Group Handoff Document

---

## Table of Contents

1. [What This Project Does](#1-what-this-project-does)
2. [Module Ownership](#2-module-ownership)
3. [Architecture Overview](#3-architecture-overview)
4. [Repository Structure](#4-repository-structure)
5. [Local Setup (First Time)](#5-local-setup-first-time)
6. [Running the Project](#6-running-the-project)
7. [API Reference](#7-api-reference)
8. [Database Schema](#8-database-schema)
9. [What Is Already Implemented](#9-what-is-already-implemented)
10. [What Needs To Be Implemented Next](#10-what-needs-to-be-implemented-next)
11. [Known Issues & Gotchas](#11-known-issues--gotchas)

---

## 1. What This Project Does

KuberNexus collects CPU and memory metrics from Kubernetes clusters via
Prometheus, analyzes whether workloads (Deployments, StatefulSets, etc.) are
over- or under-provisioned, and generates right-sizing recommendations.

The end-to-end demo flow is:

```
Register Cluster → Workload Discovery → Inspect (1 h) → Recommendations
    → Approve → Apply → Changes Audit → Evaluation
```

---

## 2. Module Ownership

| Module | Owner | Status |
|---|---|---|
| **Cluster Registration & Data Ingestion** (FR-01 – FR-05) | Mauli | ✅ Done |
| Recommendation Engine | — | 🔲 Pending |
| Approve / Apply / Rollback workflow | — | 🔲 Pending |
| Cost Optimization calculations | — | 🔲 Pending |
| Alerts & Notifications | — | 🔲 Pending |
| Post-Change Evaluation | — | 🔲 Pending |

---

## 3. Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│  Browser  (React + Vite, port 3000)                       │
│  src/pages/ClustersPage.tsx  ← registration form (DONE)  │
└─────────────────────────┬────────────────────────────────┘
                          │ REST / JSON
┌─────────────────────────▼────────────────────────────────┐
│  FastAPI Backend  (Python, port 8000)                     │
│  backend/app/routers/clusters.py   ← cluster CRUD         │
│  backend/app/routers/workloads.py  ← workload queries     │
│  backend/app/routers/metrics.py    ← Prometheus fetch      │
│  backend/app/services/cluster_collector.py  ← K8s SDK    │
└──────────┬───────────────────────────┬────────────────────┘
           │                           │
    ┌──────▼──────┐             ┌──────▼──────────────┐
    │  SQLite DB  │             │  Kubernetes API      │
    │ (or Postgres│             │  (Minikube / EKS…)  │
    │  /Supabase) │             └──────┬───────────────┘
    └─────────────┘                    │
                                ┌──────▼──────┐
                                │  Prometheus │
                                │  port 9090  │
                                └─────────────┘
```

---

## 4. Repository Structure

```
KuberNexus/
├── backend/
│   ├── .env                    ← local secrets (NOT committed)
│   ├── .env.example            ← template – copy to .env
│   ├── requirements.txt
│   ├── run.py                  ← starts uvicorn
│   ├── kubenexus.db            ← SQLite file (auto-created)
│   └── app/
│       ├── main.py             ← FastAPI app, CORS, router mounts
│       ├── database.py         ← SQLAlchemy engine (SQLite fallback)
│       ├── models/
│       │   ├── orm.py          ← SQLAlchemy table definitions
│       │   └── schemas.py      ← Pydantic request/response models
│       ├── routers/
│       │   ├── clusters.py     ← POST/GET /api/v1/clusters
│       │   ├── workloads.py    ← GET /api/v1/workloads
│       │   ├── metrics.py      ← GET /api/v1/metrics/{workload_id}
│       │   ├── recommendations.py
│       │   ├── alerts.py
│       │   ├── audit.py
│       │   ├── evaluation.py
│       │   └── settings.py
│       ├── services/
│       │   └── cluster_collector.py  ← Kubernetes + Prometheus client
│       └── storage/
│           └── db.py           ← DB access layer (all CRUD methods)
│
├── src/                        ← React frontend (TypeScript)
│   ├── api/index.ts            ← all fetch() calls to backend
│   ├── types/index.ts          ← shared TypeScript interfaces
│   ├── context/AppContext.tsx  ← global state
│   └── pages/
│       ├── ClustersPage.tsx    ← cluster registration form (DONE)
│       ├── WorkloadsPage.tsx
│       ├── RecommendationsPage.tsx
│       └── …
│
├── package.json                ← frontend deps (npm)
├── vite.config.ts
└── README.md                   ← this file
```

---

## 5. Local Setup (First Time)

### Prerequisites

| Tool | Version | Install |
|---|---|---|
| Node.js | ≥ 18 | https://nodejs.org |
| Python | 3.10 – 3.12 | https://python.org |
| Docker Desktop | any | https://docker.com |
| Minikube | any | https://minikube.sigs.k8s.io |
| kubectl | any | bundled with Docker Desktop |

### Backend

```powershell
cd backend

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Create your .env (leave DATABASE_URL blank to use SQLite)
Copy-Item .env.example .env
```

### Frontend

```powershell
# From the project root (KuberNexus/)
npm install
```

### Kubernetes (Minikube)

```powershell
# Start Minikube
minikube start

# Install Prometheus stack (only needed once)
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
kubectl create namespace monitoring
helm install kube-prometheus prometheus-community/kube-prometheus-stack -n monitoring
```

---

## 6. Running the Project

Open **three separate terminals** and run one command in each:

### Terminal 1 — Prometheus port-forward

```powershell
kubectl port-forward -n monitoring svc/kube-prometheus-kube-prome-prometheus 9090:9090
```

Keep this running. Prometheus metrics will be available at http://localhost:9090.

### Terminal 2 — Backend

```powershell
cd "KuberNexus\backend"
.\.venv\Scripts\Activate.ps1
python run.py
```

Backend starts at http://localhost:8000.  
Interactive API docs: http://localhost:8000/docs

### Terminal 3 — Frontend

```powershell
cd KuberNexus
npm.cmd run dev        # use npm.cmd on Windows PowerShell
```

Frontend starts at http://localhost:3000.

> **Note for Windows users:** Use `npm.cmd` instead of `npm` in PowerShell
> to avoid execution-policy errors.

---

## 7. API Reference

All endpoints are prefixed with `/api/v1`. Full interactive docs at
http://localhost:8000/docs when the backend is running.

### Clusters

| Method | Path | Description |
|---|---|---|
| `GET` | `/clusters` | List all registered clusters |
| `GET` | `/clusters/{id}` | Get a single cluster |
| `POST` | `/clusters` | Register a new cluster (verifies connection first) |
| `GET` | `/clusters/{id}/workloads` | Re-discover workloads from live Kubernetes |

#### POST `/clusters` — Request Body

```jsonc
{
  "name": "My Cluster",
  "environment": "staging",       // "production" | "staging" | "development"
  "provider": "Self-Hosted Minikube",
  "authMethod": "local",          // "local" | "kubeconfig" | "token"
  "apiEndpoint": null,            // optional — auto-detected for "local"
  "kubeconfigRaw": null,          // paste full kubeconfig YAML (for "kubeconfig")
  "bearerToken": null,            // Bearer token string (for "token")
  "prometheusUrl": "http://localhost:9090"
}
```

### Workloads

| Method | Path | Description |
|---|---|---|
| `GET` | `/workloads` | All workloads across all clusters |
| `GET` | `/workloads/{id}` | Single workload |
| `POST` | `/workloads/{id}/analyze` | Trigger Prometheus metric collection + analysis |

### Metrics

| Method | Path | Description |
|---|---|---|
| `GET` | `/metrics/{workload_id}?range=24h` | Stored time-series (CPU + memory) |
| `POST` | `/metrics/{workload_id}/collect?range=24h` | Pull fresh data from Prometheus |

### Recommendations

| Method | Path | Description |
|---|---|---|
| `GET` | `/recommendations` | All recommendations |
| `GET` | `/recommendations/{id}` | Single recommendation |
| `PATCH` | `/recommendations/{id}/approve` | Approve |
| `PATCH` | `/recommendations/{id}/reject` | Reject |
| `PATCH` | `/recommendations/{id}/apply` | Apply (calls `kubectl patch`) |

### Other

| Method | Path | Description |
|---|---|---|
| `GET` | `/alerts` | Active alerts |
| `GET` | `/alerts/stream` | SSE stream for real-time alerts |
| `GET` | `/audit` | Change audit log |
| `GET` | `/evaluation` | Post-change evaluations |
| `GET/PUT` | `/settings` | Optimization settings |

---

## 8. Database Schema

The app auto-creates all tables on startup. Below are the key tables.

### `clusters`

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | `cluster-<uuid12>` |
| `name` | TEXT | User-provided name |
| `auth_method` | TEXT | `local` / `kubeconfig` / `token` |
| `api_endpoint` | TEXT | Kubernetes API server URL |
| `kubeconfig_raw` | TEXT | Stored YAML (nullable) |
| `bearer_token` | TEXT | Bearer token (nullable) |
| `prometheus_url` | TEXT | Per-cluster Prometheus URL |
| `k8s_version` | TEXT | Detected from live cluster |
| `node_count` | INT | Detected from live cluster |

### `workloads`

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | `workload-<sha256[:48]>` — stable across restarts |
| `cluster_id` | TEXT FK | → `clusters.id` |
| `type` | TEXT | `Deployment` / `StatefulSet` / `DaemonSet` / `Job` |
| `cpu_request_cores` | FLOAT | Parsed from K8s resource spec |
| `cpu_usage_cores` | FLOAT | Latest Prometheus value |
| `cpu_utilization_pct` | FLOAT | usage / request × 100 |

### `metric_samples`

Stores raw Prometheus time-series data points.

| Column | Type | Notes |
|---|---|---|
| `id` | TEXT PK | SHA-256 of `workload_id + timestamp` |
| `workload_id` | TEXT FK | → `workloads.id` |
| `timestamp` | TEXT | ISO 8601 |
| `cpu_usage` | FLOAT | cores |
| `memory_usage_mb` | FLOAT | MB |

---

## 9. What Is Already Implemented

### ✅ FR-01 — Cluster Registration Form
- `src/pages/ClustersPage.tsx` — 3-tab auth modal (Local / Kubeconfig YAML / Bearer Token)
- File upload for kubeconfig, Prometheus URL field, loading state

### ✅ FR-02 — Credential Verification
- `backend/app/services/cluster_collector.py → ClusterCollector.verify()`
- Calls live Kubernetes API before saving; returns node count, K8s version
- Returns HTTP 400 with a clear message on auth failure

### ✅ FR-03 — Workload Discovery
- `ClusterCollector.discover()` — lists Deployments, StatefulSets, DaemonSets, Jobs
- Stable workload IDs based on `cluster:namespace:kind:name` hash
- Pod-level restart & OOMKill counts collected

### ✅ FR-04 — Prometheus Metrics Collection
- `ClusterCollector.metrics()` — queries `container_cpu_usage_seconds_total` and
  `container_memory_working_set_bytes` via range API
- `POST /metrics/{workload_id}/collect` triggers a live pull

### ✅ FR-05 — Persistent Storage
- SQLite (default) or PostgreSQL/Supabase (optional)
- `backend/app/storage/db.py` — full CRUD for all entities
- `get_cluster_credentials(cluster_id)` — retrieves stored auth securely server-side

### ✅ Database Fallback
- If `DATABASE_URL` is blank or connection fails, app auto-falls back to local SQLite
- No configuration needed for dev/demo

---

## 10. What Needs To Be Implemented Next

### 🔲 Recommendation Engine (`POST /workloads/{id}/analyze`)

**File:** `backend/app/routers/workloads.py` — the `/analyze` endpoint already exists
but calls a stub. Implement in `backend/app/services/`.

**Logic needed:**
1. Fetch stored `metric_samples` for the workload (last 7–14 days)
2. Compute percentiles: p50, p90, p99 of CPU and memory
3. Apply safety margin (from Settings, default 20%)
4. If `usage_p90 * (1 + safety_margin) < current_request` → over-provisioned
5. Create a `Recommendation` object and call `db.save_recommendation(rec)`

**Pydantic schema** is ready in `schemas.py → Recommendation`.  
**DB method** is ready: `db.save_recommendation(rec)`.

---

### 🔲 Apply Recommendation (`PATCH /recommendations/{id}/apply`)

**File:** `backend/app/routers/recommendations.py`

**Logic needed:**
1. Load recommendation from DB
2. Patch the Kubernetes deployment using the stored cluster credentials:
   ```python
   creds = db.get_cluster_credentials(cluster_id)
   # Use cluster_collector._kubernetes_clients(**creds) to get apps_api
   apps_api.patch_namespaced_deployment(name, namespace, body)
   ```
3. Update recommendation status → `"Applied"` in DB
4. Create an `AuditEvent` entry via `db.add_audit_event()`

---

### 🔲 Post-Change Evaluation

**File:** `backend/app/routers/evaluation.py`

After applying a recommendation, collect metrics again after 24–48 hours and
compare before/after utilization. Schema is ready: `PostChangeEvaluation`.

---

### 🔲 Cost Optimization Page

**File:** `src/pages/CostOptimizationPage.tsx`

Needs a backend endpoint `GET /api/v1/cost-summary` that aggregates:
- Sum of `estimatedMonthlySavings` across all pending recommendations
- Count of over/under-provisioned workloads

---

### 🔲 Real-time Alerts

**File:** `backend/app/routers/alerts.py`

The SSE stream (`/alerts/stream`) exists. Feed it by:
1. Running a background task (FastAPI `BackgroundTasks` or `asyncio`) that
   periodically checks workload utilization
2. Creating `AlertItem` objects and pushing to the SSE queue

---

## 11. Known Issues & Gotchas

### Windows PowerShell — use `npm.cmd`
```powershell
# Wrong (may fail on PowerShell):
npm run dev

# Correct:
npm.cmd run dev
```

### Minikube port changes on restart
Each `minikube start` picks a new port (e.g., `https://127.0.0.1:63078`).
The `verify()` method already handles this — it allows any loopback-to-loopback
endpoint match, so you don't need to update the DB.

### SQLite is for development only
`backend/kubenexus.db` works fine for demos. For production, set a real
`DATABASE_URL` in `backend/.env`.

### Credentials stored in plaintext
`kubeconfig_raw` and `bearer_token` are stored as plain text in SQLite.
**Acceptable for a classroom prototype.** For production, encrypt at rest.

### `psycopg2-binary` vs `psycopg`
The venv currently has both installed. Both work. `psycopg2-binary` is listed
in `requirements.txt` for simplicity. If a teammate gets a build error on Linux,
they can switch to `psycopg[binary]>=3.0.0` instead.
