"""Package smoke test: the distribution installs and exposes a version."""

import kpi_api


def test_version_is_set() -> None:
    assert kpi_api.__version__ == "0.1.0"
