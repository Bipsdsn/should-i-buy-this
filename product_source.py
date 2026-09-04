"""Product data source: demo catalog (primary, evaluator happy path) + best-effort live PDP.

M0: demo-catalog loader + ProductData shape. Live scrape + creator/image refs land in M2.
"""
from __future__ import annotations
import json
import os
from typing import TypedDict

_HERE = os.path.dirname(__file__)
_CATALOG_PATH = os.path.join(_HERE, "demo_catalog.json")


class Review(TypedDict):
    text: str
    rating: int


class ProductData(TypedDict, total=False):
    id: str
    title: str
    brand: str
    category: str
    size_chart: dict          # e.g. {"S": {"chest_in": 38}, ...}
    details: str
    reviews: list[Review]
    rating: float
    image_url: str
    illustrative_photos: list[str]   # clearly-labelled, not real customers (v3 §2.4)
    source: str                      # "demo" | "live"


def load_catalog() -> list[ProductData]:
    with open(_CATALOG_PATH, encoding="utf-8") as f:
        return json.load(f)


def get_product(id_or_url: str) -> ProductData:
    """Return a ProductData. M0: demo-catalog only. Live PDP scrape added in M2."""
    catalog = {p["id"]: p for p in load_catalog()}
    if id_or_url in catalog:
        return catalog[id_or_url]
    # TODO(M2): scrape live PDP for a Myntra URL; for now fall back to first demo item.
    first = load_catalog()[0]
    return first
