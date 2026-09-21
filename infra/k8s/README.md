# Generic Kubernetes manifests

Provider-agnostic: no cloud-specific resources. Apply with kustomize after setting your image
registry in `kustomization.yaml` and creating the `kpi-secrets` Secret (see `secret.example.yaml`).

```bash
kubectl apply --dry-run=client -k infra/k8s      # validate
kubectl apply -k infra/k8s                        # deploy
kubectl -n zairus wait --for=condition=complete job/kpi-migrate --timeout=300s
kubectl -n zairus get pods
```

Rollout order is enforced by readiness: `api`'s `/readyz` checks the database and the MCP
service, so it stays unready until `mcp` is up and the migration job has completed. The chat-web
nginx config proxies `/api/` to the `api` Service; with the ingress above the same path works
through the ingress as well.

Scaling: `api` and `mcp` are stateless; note the per-replica in-process rate limiter (ADR-0010).
Use a managed Postgres in production and remove `postgres.yaml` from the kustomization.
