# k8s-multi-service-app

A microservices notes application with:
- `auth-service` (FastAPI + JWT)
- `notes-service` (FastAPI + JWT validation)
- `notification-service` (FastAPI + Redis pub/sub listener)
- `frontend` (React + Vite, served with Nginx)
- `redis` (state/pub-sub backbone)

## Architecture

- Frontend calls backend through Ingress routes.
- Auth service issues JWT tokens.
- Notes service validates JWT and publishes note events to Redis.
- Notification service subscribes to Redis `note_events`.

## Repository Structure

- `auth-service/` - user register/login and token issuance
- `notes-service/` - CRUD for notes (JWT protected)
- `notification-service/` - background Redis subscriber
- `frontend/` - React UI
- `k8s/` - Kubernetes manifests (deployments, services, ingress, hpa, policies)
- `docker-compose.yml` - local multi-container stack

## Prerequisites

- Docker Desktop
- Kubernetes cluster (GKE or local)
- `kubectl`
- `gcloud` CLI (for GKE)

## Run Locally (Docker Compose)

From project root:

```bash
docker compose up -d --build
```

App endpoints:
- Frontend: `http://localhost:5173`
- Auth service: `http://localhost:8000`
- Notes service: `http://localhost:8001`

Stop:

```bash
docker compose down
```

## Build and Push Images (Artifact Registry)

Example (replace tags as needed):

```bash
docker build -t us-central1-docker.pkg.dev/sandbox-akumar/k8s-microservices/auth-service:v3 ./auth-service
docker build -t us-central1-docker.pkg.dev/sandbox-akumar/k8s-microservices/notes-service:v3 ./notes-service
docker build -t us-central1-docker.pkg.dev/sandbox-akumar/k8s-microservices/notification-service:v3 ./notification-service
docker build -t us-central1-docker.pkg.dev/sandbox-akumar/k8s-microservices/frontend:v3 ./frontend

docker push us-central1-docker.pkg.dev/sandbox-akumar/k8s-microservices/auth-service:v3
docker push us-central1-docker.pkg.dev/sandbox-akumar/k8s-microservices/notes-service:v3
docker push us-central1-docker.pkg.dev/sandbox-akumar/k8s-microservices/notification-service:v3
docker push us-central1-docker.pkg.dev/sandbox-akumar/k8s-microservices/frontend:v3
```

## Kubernetes Deploy

1. Ensure context is correct:

```bash
kubectl config current-context
kubectl get nodes
```

2. Create namespace:

```bash
kubectl create namespace notes-app --dry-run=client -o yaml | kubectl apply -f -
```

3. Apply manifests:

```bash
kubectl apply -n notes-app -f k8s/redis.yaml
kubectl apply -n notes-app -f k8s/configmap.yaml
kubectl apply -n notes-app -f k8s/auth-service.yaml
kubectl apply -n notes-app -f k8s/notes-service.yaml
kubectl apply -n notes-app -f k8s/notification-service.yaml
kubectl apply -n notes-app -f k8s/frontend-service.yaml
kubectl apply -n notes-app -f k8s/network-policies.yaml
kubectl apply -n notes-app -f k8s/hpa.yaml
kubectl apply -f k8s/ingress.yaml
```

4. Verify:

```bash
kubectl get pods -n notes-app
kubectl get svc -n notes-app
kubectl get ingress -n notes-app
kubectl get hpa -n notes-app
```

## Ingress Routes

Configured paths:
- `/api/auth/*` -> auth-service
- `/api/notes/*` -> notes-service
- `/` -> frontend

## Load Test Example

```bash
docker run --rm williamyeh/hey -n 1000 -c 50 http://<INGRESS_IP>/api/notes/health
```

JWT-protected route test:

```bash
docker run --rm williamyeh/hey -n 1000 -c 50 -H "Authorization: Bearer <JWT_TOKEN>" http://<INGRESS_IP>/api/notes/notes
```

## Common Troubleshooting

- `x509: certificate signed by unknown authority` with `kubectl`:
  - refresh credentials with `gcloud container clusters get-credentials ...`
- HPA shows `cpu: <unknown>`:
  - ensure all target pods have CPU requests
  - ensure rollout is complete (no stale ReplicaSet pods)
- `Insufficient cpu` scheduling errors:
  - increase node count or enable node autoscaling
- Ingress regex errors with `Prefix`:
  - use `pathType: ImplementationSpecific`
  - set `nginx.ingress.kubernetes.io/use-regex: "true"`

## Notes

- Redis image is public (`redis:7-alpine`) and does not need custom push.
- Use versioned image tags (`v1`, `v2`, `v3`) instead of `latest` for predictable deploys.
