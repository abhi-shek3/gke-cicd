# Cloud-Native Microservices Application on Kubernetes (GKE)

A production-grade, cloud-native microservices application deployed on **Google Kubernetes Engine (GKE)**. Demonstrates end-to-end DevOps practices including containerization, CI/CD pipeline automation, Kubernetes orchestration, event-driven architecture, Zero Trust network security, autoscaling, and GitOps continuous delivery.

---

## Tech Stack

### Backend
| Technology | Purpose |
|---|---|
| Python 3.13 | Application runtime |
| FastAPI | RESTful API framework with OpenAPI/Swagger docs |
| JWT (JSON Web Tokens) | Stateless authentication (`python-jose`) |
| bcrypt / passlib | Secure password hashing |
| Redis Pub/Sub | Async event-driven messaging between microservices |
| Pydantic v2 | Data validation and schema enforcement |

### Frontend
| Technology | Purpose |
|---|---|
| React 18 | Component-based SPA |
| Vite | Frontend build tooling |
| Axios | HTTP client |
| Nginx | Static file serving inside container |

### Infrastructure & DevOps
| Technology | Purpose |
|---|---|
| Docker | Containerization of all services |
| Docker Compose | Local multi-container development environment |
| Kubernetes (K8s) | Container orchestration |
| Google Kubernetes Engine (GKE) | Managed Kubernetes on GCP |
| Google Artifact Registry | Private Docker image registry |
| GitHub Actions | CI pipeline — build and push images on every merge to `main` |
| ArgoCD | GitOps continuous delivery — cluster state synced from Git |
| Helm | Kubernetes package manager |

### Kubernetes Features Implemented
- **Deployments** with rolling update strategy (`maxUnavailable: 1`, `maxSurge: 1`)
- **Services (ClusterIP)** — internal service discovery via Kubernetes DNS
- **Ingress (Nginx Ingress Controller)** — single public entry point with path-based routing and URL rewriting
- **ConfigMap** — externalized environment configuration
- **Secrets** — secure injection of sensitive values (JWT secret key) via `secretKeyRef`
- **Horizontal Pod Autoscaler (HPA)** — CPU-based autoscaling (min: 2 → max: 8 replicas)
- **NetworkPolicy** — Zero Trust security model (default deny-all, explicit allow rules per service)
- **PodDisruptionBudget (PDB)** — guaranteed pod availability during node maintenance and upgrades
- **Topology Spread Constraints** — pod distribution across nodes for infrastructure fault tolerance
- **Liveness, Readiness & Startup Probes** — self-healing containers and safe rolling deployments
- **Resource Requests & Limits** — CPU/memory governance per container

---

## Architecture

```
Internet
    |
    v
Nginx Ingress Controller  (single public IP)
    |
    |-- /api/auth/*  -->  auth-service      (FastAPI, 3 replicas, JWT issuance)
    |-- /api/notes/* -->  notes-service     (FastAPI, 3 replicas, JWT validation)
    `-- /            -->  frontend-service  (React + Nginx, 1 replica)
                                |
                                v
                            Redis (Pub/Sub)
                                |
                                v
                     notification-service   (async background listener, 1 replica)
```

**Authentication flow:** `auth-service` signs JWT tokens with a shared secret injected via Kubernetes Secret → `notes-service` verifies tokens independently using the same secret (stateless, no inter-service HTTP calls needed).

**Event flow:** `notes-service` publishes to Redis `note_events` channel on every note creation → `notification-service` subscribes and processes events asynchronously via `asyncio`.

---

## Repository Structure

```
k8s-multi-service-app/
├── auth-service/            # User registration, login, JWT issuance
│   ├── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── notes-service/           # CRUD notes API (JWT-protected), Redis publisher
│   ├── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── notification-service/    # Async Redis Pub/Sub event listener
│   ├── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                # React SPA served via Nginx
├── k8s/                     # Kubernetes manifests
│   ├── configmap.yaml       # Shared environment config
│   ├── auth-service.yaml    # Deployment + ClusterIP Service
│   ├── notes-service.yaml   # Deployment + ClusterIP Service + probes
│   ├── notification-service.yaml
│   ├── frontend-service.yaml
│   ├── redis.yaml
│   ├── ingress.yaml         # Nginx Ingress with path-based routing
│   ├── hpa.yaml             # Horizontal Pod Autoscaler
│   ├── network-policies.yaml # Zero Trust firewall rules
│   └── pdb.yaml             # PodDisruptionBudgets
├── .github/workflows/       # GitHub Actions CI pipeline
│   └── ci.yaml
├── argo-application.yaml    # ArgoCD GitOps application config
└── docker-compose.yml       # Local development stack
```

---

## Security Implementation

- **Zero Trust NetworkPolicy**: default-deny-all ingress on the `notes-app` namespace; explicit allow rules for each required service-to-service path only
- **Kubernetes Secrets**: JWT secret key injected at pod runtime via `secretKeyRef` — never present in source code or ConfigMaps
- **bcrypt password hashing**: passwords stored only as hashed values; 72-byte input length validation enforced before hashing
- **Stateless JWT authentication**: tokens cryptographically verified on each request — no server-side session storage required
- **ClusterIP-only services**: no service is directly internet-exposed; all external traffic routes exclusively through the Nginx Ingress Controller

---

## CI/CD Pipeline

**GitHub Actions** (`.github/workflows/ci.yaml`):
- Triggers on push to `main` for changes in any service directory
- Authenticates to GCP via `google-github-actions/auth`
- Builds and pushes Docker images to Google Artifact Registry

**ArgoCD** (`argo-application.yaml`):
- Watches this Git repository for changes to `k8s/` manifests
- Automatically syncs the live GKE cluster state to match Git — GitOps model
- Eliminates manual `kubectl apply` from the deployment workflow

---

## Run Locally (Docker Compose)

```bash
docker compose up -d --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Auth Service (Swagger UI) | http://localhost:8000/docs |
| Notes Service (Swagger UI) | http://localhost:8001/docs |

```bash
docker compose down
```

---

## Deploy to GKE

### 1. Authenticate
```bash
gcloud auth configure-docker us-central1-docker.pkg.dev
gcloud container clusters get-credentials <CLUSTER_NAME> --region <REGION>
```

### 2. Build & Push Images
```bash
docker build -t us-central1-docker.pkg.dev/<PROJECT_ID>/k8s-microservices/auth-service:v1 ./auth-service
docker push us-central1-docker.pkg.dev/<PROJECT_ID>/k8s-microservices/auth-service:v1
# repeat for notes-service, notification-service, frontend
```

### 3. Apply Manifests
```bash
kubectl create namespace notes-app
kubectl apply -f k8s/
```

### 4. Verify
```bash
kubectl get pods -n notes-app
kubectl get ingress -n notes-app
kubectl get hpa -n notes-app
```

---

## Ingress Routes

| Path | Backend Service | Port |
|---|---|---|
| `/api/auth/*` | auth-service | 8000 |
| `/api/notes/*` | notes-service | 8000 |
| `/` | frontend-service | 80 |

---

## Load Testing (HPA Trigger)

```bash
# Simulate 10,000 requests at 50 concurrency — triggers HPA scale-up
docker run --rm williamyeh/hey -n 10000 -c 50 http://<INGRESS_IP>/api/notes/health
```

Watch autoscaler respond in real time:
```bash
kubectl get hpa notes-hpa -n notes-app -w
```

---

## Common Troubleshooting

- **`x509: certificate signed by unknown authority`** with `kubectl`: refresh credentials with `gcloud container clusters get-credentials ...`
- **HPA shows `cpu: <unknown>`**: ensure all target pods have CPU `requests` set and rollout is fully complete
- **`Insufficient cpu` scheduling errors**: increase node count or enable GKE node autoprovisioning
- **Ingress 404 on regex paths**: use `pathType: ImplementationSpecific` and set annotation `nginx.ingress.kubernetes.io/use-regex: "true"`

---

## Notes

- Redis uses the public `redis:7-alpine` image from Docker Hub — no custom build or push required
- Use versioned image tags (`v1`, `v2`, `v3`) rather than `latest` for reproducible and rollback-safe deployments
