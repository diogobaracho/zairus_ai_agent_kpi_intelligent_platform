# Add a database migration

1. Change the ORM in `packages/kpi_core/src/kpi_core/db/orm.py`.
2. `cd packages/kpi_core && uv run alembic revision --autogenerate -m "add sector summary"`
   (uses `KPI_DATABASE_URL`; run against `make up`'s Postgres).
3. Review the generated file under `db/migrations/versions/`: autogenerate misses partial
   indexes, CHECK constraints and `NULLS NOT DISTINCT`; write them explicitly.
4. Add a downgrade that really reverses the change.
5. Run `make migrate`, then `uv run pytest -m integration -k migrations` (up → down → up).
6. If the seed needs new columns, update `seed/csv_loader.py`/`seeder.py` and re-run
   `make seed` (idempotent).
7. Update `docs/data-model.md`.

## Verify

```bash
make migrate                                   # Running upgrade 0001 -> 0002
uv run pytest -m integration -k "migrations or seed" -q
```

## What usually goes wrong

- Autogenerate produces an empty migration: the ORM module was not imported in `env.py`.
- Migration works locally but not in the container: the container entrypoint runs
  `alembic upgrade head` with `KPI_DATABASE_URL` pointing at the `postgres` service hostname.
