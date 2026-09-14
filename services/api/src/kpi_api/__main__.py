"""`python -m kpi_api` runs uvicorn with settings from the environment."""

from __future__ import annotations

import uvicorn

from kpi_api.settings import ApiSettings


def main() -> None:
    settings = ApiSettings()
    uvicorn.run(
        "kpi_api.app:create_app",
        factory=True,
        host=settings.api_host,
        port=settings.api_port,
        log_config=None,
    )


if __name__ == "__main__":
    main()
