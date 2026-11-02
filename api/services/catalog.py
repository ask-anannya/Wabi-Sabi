"""
Curated product catalog (api/data/products.json) and editorial brand
signals (api/data/brands.json). Loaded once. Products are the factual side of
the trust engine (actives, concentrations, prices); brands.json carries the
editorial buzz tier and style tags, labelled as editorial in the UI.
"""

import json
import os
import statistics
from functools import lru_cache

from domain.actives import rung_for, rung_label
from models.profile import Product, ProductSummary

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
CATALOG_PATH = os.path.join(DATA_DIR, "products.json")
BRANDS_PATH = os.path.join(DATA_DIR, "brands.json")
STYLES = ["budget", "derm", "clean", "k-beauty", "luxury", "pharmacy"]


@lru_cache(maxsize=1)
def all_products() -> dict[str, Product]:
    with open(CATALOG_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    return {p["id"]: Product(**p) for p in raw["products"]}


def get(product_id: str) -> Product | None:
    return all_products().get(product_id)


def rungs(product: Product) -> dict[str, int]:
    """Strongest rung per active family in this product."""
    out: dict[str, int] = {}
    for a in product.actives:
        r = rung_for(a.family, a.form, a.pct, product.rinse_off)
        out[a.family] = max(out.get(a.family, 0), r)
    return out


def value_group(product: Product) -> str:
    # Active products compete with the same active; everything else with its category.
    return f"active:{product.primary_family}" if product.primary_family else f"category:{product.category}"


@lru_cache(maxsize=1)
def group_medians() -> dict[str, float]:
    groups: dict[str, list[float]] = {}
    for p in all_products().values():
        groups.setdefault(value_group(p), []).append(p.price_per_ml)
    return {g: statistics.median(v) for g, v in groups.items()}


def strength_labels(product: Product) -> list[str]:
    labels = []
    for family, rung in rungs(product).items():
        label = rung_label(family, rung)
        if any(a.family == family and a.pct is None for a in product.actives):
            label += " (strength undisclosed)"
        labels.append(label)
    return labels


def summary(product: Product) -> ProductSummary:
    return ProductSummary(
        id=product.id,
        brand=product.brand,
        name=product.name,
        category=product.category,
        price_usd=product.price_usd,
        size_ml=product.size_ml,
        key_ingredients=product.key_ingredients,
        strength=strength_labels(product),
    )


def brands() -> list[str]:
    return sorted({p.brand for p in all_products().values()})


@lru_cache(maxsize=1)
def _brands_file() -> dict:
    with open(BRANDS_PATH, encoding="utf-8") as f:
        return json.load(f)


def brand_signals() -> dict[str, dict]:
    return _brands_file()["brands"]


def buzz_level(brand: str) -> str | None:
    return (brand_signals().get(brand) or {}).get("buzz")


def buzz_score(brand: str) -> float | None:
    level = buzz_level(brand)
    return _brands_file()["buzz_levels"].get(level) if level else None


def brand_styles(brand: str) -> set[str]:
    return set((brand_signals().get(brand) or {}).get("styles", []))
