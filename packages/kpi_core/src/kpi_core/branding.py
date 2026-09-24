"""White-label branding: product name, data provider and contact details from one JSON file.

Lookup order: `KPI_BRAND_CONFIG` (path) -> `brand.config.json` in the working directory or any
parent -> built-in defaults. A missing file is never an error, so a single service can be deployed
without the rest of the repository. The same file feeds the web apps at build time.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

CONFIG_FILENAME = "brand.config.json"


class _Model(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore", populate_by_name=True)


class Address(_Model):
    street: str = ""
    city: str = ""
    region: str = ""
    postal_code: str = Field(default="", alias="postalCode")
    country: str = ""


class Contact(_Model):
    email: str = "hello@example.com"
    phone: str = ""
    address: Address = Address()


class Brand(_Model):
    brand: str = "KPI Platform"
    product: str = "KPI Intelligent Platform"
    data_provider: str = Field(default="the data provider", alias="dataProvider")
    assistant_name: str = Field(default="KPI assistant", alias="assistantName")
    mcp_server_name: str = Field(default="kpi-platform", alias="mcpServerName")
    contact: Contact = Contact()


def find_brand_config(start: Path | None = None) -> Path | None:
    explicit = os.environ.get("KPI_BRAND_CONFIG")
    if explicit:
        path = Path(explicit)
        return path if path.is_file() else None
    here = (start or Path.cwd()).resolve()
    for folder in (here, *here.parents):
        candidate = folder / CONFIG_FILENAME
        if candidate.is_file():
            return candidate
    return None


def load_brand(path: Path | None) -> Brand:
    if path is None:
        return Brand()
    return Brand.model_validate(json.loads(path.read_text(encoding="utf-8")))


@lru_cache(maxsize=1)
def get_brand() -> Brand:
    """Read once, cache; `get_brand.cache_clear()` in tests."""
    return load_brand(find_brand_config())
