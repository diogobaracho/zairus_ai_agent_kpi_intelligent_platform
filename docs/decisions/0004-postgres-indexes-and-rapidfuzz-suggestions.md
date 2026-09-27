# ADR-0004: Postgres 16 with functional/trigram indexes; suggestions computed in-process with rapidfuzz

- **Status**: Accepted
- **Date**: 2026-09-24

## Context

Partial-name search must be fast and case-insensitive; misspellings must yield suggestions;
the same suggestions must come from the in-memory test repository and the SQL repository.

## Decision

Postgres 16 with `lower(name)` and `pg_trgm` GIN indexes for `%q%` search, partial indexes for
history and latest-QTD lookups, and `UNIQUE NULLS NOT DISTINCT` for the idempotent natural key.
Fuzzy suggestions (tickers, names, KPI names, sectors) use rapidfuzz over small cached candidate
lists plus an alias table, inside `kpi_core.fuzzy`, independent of the storage engine.

## Alternatives considered

| Option | Why not |
|---|---|
| `similarity()` in SQL for suggestions | Splits suggestion logic between two repos; alias handling is domain logic |
| SQLite for tests | Diverges from production SQL; testcontainers/Postgres service is cheap |
| No trigram index | Fine at a few dozen companies, but the index costs nothing and documents the 100x path |

## Consequences

- **Good**: identical suggestions everywhere; sub-millisecond lookups; idempotent seed.
- **Bad**: candidate lists are cached in memory (60 s) and would need invalidation with live ingestion.
- **Unverified**: rapidfuzz scores on real-world typos beyond the test set.

## Revisit if

Candidate lists exceed a few thousand rows; then move to trigram similarity in SQL.
