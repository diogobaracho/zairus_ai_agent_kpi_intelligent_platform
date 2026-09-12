from __future__ import annotations

from pathlib import Path

import pytest

from kpi_core.context import RequestContext
from kpi_core.repositories.memory import InMemoryKpiRepository


@pytest.fixture(scope="session")
def memory_repo(sample_csv_path: Path, edge_cases_csv_path: Path) -> InMemoryKpiRepository:
    return InMemoryKpiRepository.from_csv(sample_csv_path, edge_cases_csv_path)


@pytest.fixture
def ctx() -> RequestContext:
    return RequestContext(trace_id="test-trace-0001", caller="test")
