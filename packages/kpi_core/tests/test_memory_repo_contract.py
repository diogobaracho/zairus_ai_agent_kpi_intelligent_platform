import pytest

from kpi_core.repositories.memory import InMemoryKpiRepository
from kpi_core.testing.contract import KpiRepositoryContract


class TestInMemoryRepositoryContract(KpiRepositoryContract):
    @pytest.fixture
    async def repo(self, memory_repo: InMemoryKpiRepository) -> InMemoryKpiRepository:
        return memory_repo
