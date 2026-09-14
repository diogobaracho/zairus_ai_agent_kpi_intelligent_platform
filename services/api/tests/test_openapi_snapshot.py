"""The OpenAPI document is part of the contract; regenerate with UPDATE_SNAPSHOTS=1."""

import json
import os
from pathlib import Path

from fastapi import FastAPI

SNAPSHOT = Path(__file__).parent / "snapshots" / "openapi.json"


def test_openapi_matches_snapshot(app: FastAPI) -> None:
    current = json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n"
    if os.environ.get("UPDATE_SNAPSHOTS") == "1" or not SNAPSHOT.exists():
        SNAPSHOT.write_text(current)
    assert current == SNAPSHOT.read_text(), (
        "OpenAPI changed: review and run with UPDATE_SNAPSHOTS=1"
    )
