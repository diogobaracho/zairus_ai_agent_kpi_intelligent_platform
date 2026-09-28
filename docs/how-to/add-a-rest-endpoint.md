# Add a REST endpoint

Example: `GET /v1/sectors/{sector}/summary` (average latest QTD per KPI across the sector).

1. Service function in `kpi_core/services` (raise `SectorNotFound` with suggestions).
2. Response model in `services/api/src/kpi_api/schemas/`.
3. Route in the matching router (`routers/sectors.py`): validate path/query with pydantic,
   build `ctx` via `Depends(get_context)`, call the service, return the model. No logic here.
4. Tests in `services/api/tests/test_sectors_routes.py`: 200 shape, 404 problem+json with
   `code`, `suggestions` and `trace_id`, and the `X-Correlation-Id` echo.
5. Update the OpenAPI snapshot (`UPDATE_SNAPSHOTS=1 uv run pytest services/api -k openapi`) and
   `docs/reference/rest-api.md`.

## Verify

```bash
uv run pytest services/api -q
curl -si localhost:8080/v1/sectors/Software/summary | head -1   # HTTP/1.1 200 OK
curl -s localhost:8080/v1/sectors/Sofware/summary | jq .suggestions
```

## What usually goes wrong

- Returning a dict: FastAPI will not validate it; always return the response model.
- Catching `KpiError` in the route: let the exception handler produce the problem document.
