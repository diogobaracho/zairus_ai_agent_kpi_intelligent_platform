import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kpi_core.repositories.sqlalchemy_repo import SqlAlchemyKpiRepository
from kpi_core.testing.contract import KpiRepositoryContract

pytestmark = pytest.mark.integration


class TestSqlRepositoryContract(KpiRepositoryContract):
    @pytest.fixture
    async def repo(self, sql_sessions: async_sessionmaker[AsyncSession]) -> SqlAlchemyKpiRepository:
        return SqlAlchemyKpiRepository(sql_sessions)
