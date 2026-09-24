import json
from pathlib import Path

import pytest

from kpi_core.branding import Brand, find_brand_config, get_brand, load_brand

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_repo_config_is_found_from_a_subfolder(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KPI_BRAND_CONFIG", raising=False)
    path = find_brand_config(REPO_ROOT / "packages" / "kpi_core")
    assert path == REPO_ROOT / "brand.config.json"
    brand = load_brand(path)
    assert brand.product and brand.data_provider and "@" in brand.contact.email


def test_env_override_and_camel_case_keys(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    custom = tmp_path / "acme.json"
    custom.write_text(
        json.dumps(
            {
                "brand": "Northwind",
                "product": "Northwind Metrics",
                "dataProvider": "Northwind Research",
                "contact": {"email": "ir@northwind.test", "address": {"postalCode": "12345"}},
                "unknownKey": "ignored",
            }
        )
    )
    monkeypatch.setenv("KPI_BRAND_CONFIG", str(custom))
    get_brand.cache_clear()
    try:
        brand = get_brand()
        assert (brand.brand, brand.data_provider) == ("Northwind", "Northwind Research")
        assert brand.contact.address.postal_code == "12345"
    finally:
        get_brand.cache_clear()


def test_missing_file_falls_back_to_defaults(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("KPI_BRAND_CONFIG", str(tmp_path / "nope.json"))
    assert find_brand_config() is None
    assert load_brand(None) == Brand()
