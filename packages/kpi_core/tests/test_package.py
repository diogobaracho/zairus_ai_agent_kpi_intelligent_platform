"""Package smoke test: the distribution installs and exposes a version."""

import kpi_core


def test_version_is_set() -> None:
    assert kpi_core.__version__ == "0.1.0"
