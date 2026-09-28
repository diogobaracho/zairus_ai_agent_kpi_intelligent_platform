# Deploy

Every part is a container image or a static bundle with environment-only configuration, health
endpoints and no provider SDKs. Any of AWS, GCP, Azure, a Kubernetes cluster or a single VM works,
and every part can be shipped on its own.

## Deploy one part on its own

| Part | Needs | Local (compose profile) | Production artifact |
|---|---|---|---|
| Website | nothing | `make up-website` (`--profile website`) | `infra/docker/website` image, or `apps/website/dist` on any static host |
| Backend (API + MCP + DB) | Postgres | `make up-backend` (`--profile backend`) | `api`, `mcp`, `migrate` images |
| MCP server only | Postgres | `docker compose --profile backend up mcp` | `mcp` image, or `python -m kpi_mcp --transport stdio` next to a desktop client |
| Chat app | an API URL | `make up-chat` (`--profile chat` + `backend`) | `chat-web` image with `API_UPSTREAM=https://api.example.com` |

**Website as a static site.** It makes no runtime calls; chat and API-docs links are optional.

```bash
corepack pnpm install --filter website...
VITE_CHAT_URL= VITE_API_DOCS_URL= corepack pnpm --filter website build   # empty = hide those links
# upload apps/website/dist/ to Netlify, Vercel, S3 + CloudFront, GitHub Pages, nginx...
```

The build reads `brand.config.json` from the repository root, or any file named by
`BRAND_CONFIG=/path/to/brand.json`. `links.siteUrl` (or `VITE_SITE_URL`) sets the canonical URL,
`robots.txt` and `sitemap.xml`, which are generated at build time. Configure your host to serve
`index.html` for unknown paths (SPA fallback).

**Chat app against a remote API.** The nginx config is a template; `API_UPSTREAM` is resolved per
request, so the container starts even when the API is not reachable yet.

**Branding in the Python images.** The images copy `brand.config.json` to `/app`; mount a different
file and set `KPI_BRAND_CONFIG` to rebrand without rebuilding. The web apps read the file at build
time, so rebuild them after a brand change.

## Components

| Component | Artifact | Port | Health | Needs |
|---|---|---|---|---|
| Postgres 16 | managed DB or `postgres:16-alpine` | 5432 | `pg_isready` | volume, `pg_trgm` allowed |
| Migrations | `infra/docker/migrate` image (`kpi_core.cli migrate && seed`) | – | exit 0 | `KPI_DATABASE_URL` |
| API | `infra/docker/api` image (uvicorn) | 8080 | `/healthz`, `/readyz` | DB, MCP URL, optional `ANTHROPIC_API_KEY` |
| MCP | `infra/docker/mcp` image (uvicorn, `/mcp`) | 8090 | `/healthz` | DB |
| chat-web | static `dist/` behind nginx (`infra/docker/chat-web`) | 3000 | `/` | `API_UPSTREAM`; `/api` proxied with SSE settings |
| website | static `dist/` behind nginx | 3001 | `/` | – |

Single-container option: `KPI_MCP_MODE=inprocess` runs the MCP server inside the API process
(same code, same audit) for the smallest footprint.

## Environment

All variables are listed in [../reference/configuration.md](../reference/configuration.md).
Secrets (`KPI_DATABASE_URL` password, `ANTHROPIC_API_KEY`) are injected by the platform's secret
store; images never contain them. Set `KPI_ENV=production` to enable stricter validation (no
wildcard CORS, provider must be configured).

## Reverse proxy requirements

- Route `/api/*` → API, `/mcp` → MCP (if exposed), `/` → chat-web, website on its own host.
- SSE: disable response buffering (`proxy_buffering off`), read timeout ≥ 300 s, pass
  `X-Correlation-Id`. The API also sets `X-Accel-Buffering: no` and sends keepalives every 15 s.
- SPA fallback: `try_files $uri /index.html`.

## Kubernetes (generic manifests in `infra/k8s/`)

`kustomization.yaml` composes: `namespace`, `configmap` (non-secret `KPI_*`),
`secret.example.yaml` (template for `kpi-secrets`: database URL, `ANTHROPIC_API_KEY`),
`postgres` (StatefulSet for dev/staging; drop it for a managed database), `migrate-job`
(Alembic + idempotent seed, runs before rollout), Deployments + Services for `api`, `mcp`,
`chat-web`, `website` (all `runAsNonRoot`, readiness on `/readyz` or `/`, liveness on `/healthz`),
and one Ingress with path routing and SSE-friendly annotations. Set your registry under
`images:`.

```bash
kubectl kustomize infra/k8s | head -40            # render
kubectl apply --dry-run=client --validate=false -k infra/k8s
kubectl apply -k infra/k8s
kubectl -n kpi-platform wait --for=condition=complete job/kpi-migrate --timeout=300s
```

Scale `api` and `mcp` horizontally; note the per-replica rate limiter (ADR-0010).

## Single VM with Docker Compose

`docker-compose.prod.yml` overrides the local file with registry images (`REGISTRY`, `TAG`),
`restart: unless-stopped`, and production env; `.env.production.example` lists the variables.

```bash
cp .env.production.example .env.production   # fill in secrets
docker compose --env-file .env.production -f docker-compose.yml -f docker-compose.prod.yml config -q
docker compose --env-file .env.production -f docker-compose.yml -f docker-compose.prod.yml up -d
```

Put a TLS-terminating proxy (Caddy, nginx, Traefik) in front of ports 3000 (chat), 3001 (site)
and 8080 (API); keep the SSE settings above on the proxy.

## Building and publishing images

```bash
for s in api mcp migrate chat-web website; do
  docker build -f infra/docker/$s/Dockerfile -t $REGISTRY/kpi-$s:$TAG . && docker push $REGISTRY/kpi-$s:$TAG
done
```

Images run as non-root (uid 999 for Python services, 101 for nginx) and expose one port each.

## Rollout order

1. Migrations job (idempotent; safe to re-run).
2. MCP, then API (API's `/readyz` checks MCP).
3. Static apps.

## Verify

```bash
docker build -f infra/docker/api/Dockerfile -t kpi-api . && docker run --rm kpi-api id -u   # 999
kubectl kustomize infra/k8s >/dev/null && kubectl apply --dry-run=client --validate=false -k infra/k8s
docker compose --env-file .env.production -f docker-compose.yml -f docker-compose.prod.yml config -q
WEBSITE_CHAT_URL= docker compose --profile website up -d --build && curl -fsS localhost:3001/robots.txt
curl -s https://<host>/api/readyz
```

CI runs the standalone-website check on every push (job `website-standalone`).
`kubectl apply --dry-run=client` needs a reachable API server for discovery, so run it against
your cluster.

## What usually goes wrong

- SSE works locally but stalls behind a load balancer: idle timeout below 60 s or buffering on.
- API starts before MCP: readiness fails until MCP is up; that is intended.
- Migrations run concurrently by multiple replicas: run them as a Job, not in every container.
- Chat app on Kubernetes returns 502: `API_UPSTREAM` must be a fully qualified service name
  (`http://api.<namespace>.svc.cluster.local:8080`), nginx's resolver ignores search domains.
- Website shows the default brand: the image was built before `brand.config.json` changed.
