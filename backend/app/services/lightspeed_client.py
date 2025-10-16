from __future__ import annotations

import asyncio
from typing import Dict, List, Optional

import httpx

from ..config import settings
from ..schemas import Product


LIGHTSPEED_BASE_URL = "https://api.lightspeedapp.com/API/Account"


def _parse_price_max(message: str) -> Optional[float]:
    text = message.lower()
    if "under" in text:
        try:
            # naive parse: "under $60" or "under 60"
            after = text.split("under", 1)[1].strip()
            digits = "".join(ch for ch in after if ch.isdigit() or ch == ".")
            return float(digits) if digits else None
        except Exception:
            return None
    return None


def _infer_category(message: str) -> Optional[str]:
    text = message.lower()
    for cat in [
        "bourbon",
        "whiskey",
        "whisky",
        "scotch",
        "tequila",
        "vodka",
        "rum",
        "gin",
        "wine",
        "beer",
    ]:
        if cat in text:
            return cat.capitalize()
    return None


async def _fetch_items(category: Optional[str], price_max: Optional[float], limit: int) -> List[Dict]:
    if not settings.lightspeed_api_key or not settings.lightspeed_account_id:
        return []

    headers = {
        "Authorization": f"Bearer {settings.lightspeed_api_key}",
        "Content-Type": "application/json",
    }

    params: Dict[str, str] = {
        "qtyOnHand": ">0",
        "limit": str(limit),
        "load_relations": "Category",
    }

    if category:
        params["category"] = category
    if price_max is not None:
        # Lightspeed may not support direct lte; keeping client-side filter as fallback
        params["price"] = f"<= {price_max}"

    url = f"{LIGHTSPEED_BASE_URL}/{settings.lightspeed_account_id}/Item.json"

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            return []
        data = resp.json()
        items = data.get("Item") or []
        if isinstance(items, dict):
            items = [items]
        return items


def _map_to_product(item: Dict) -> Optional[Product]:
    try:
        price = float(item.get("DefaultCost") or item.get("Prices", {}).get("DefaultPrice", 0.0))
    except Exception:
        price = 0.0

    qty = int(float(item.get("qoh") or item.get("QtyOnHand") or 0))
    if qty <= 0:
        return None

    return Product(
        sku=str(item.get("systemSku") or item.get("ItemID") or ""),
        name=str(item.get("description") or item.get("ItemDescription") or "Unnamed Item"),
        category=(item.get("Category") or {}).get("name"),
        price=price,
        qty_on_hand=qty,
        description=str(item.get("Note") or item.get("Description") or "") or None,
        metadata={},
    )


async def search_products_async(message: str, limit: int = 8) -> List[Product]:
    price_max = _parse_price_max(message)
    category = _infer_category(message)
    items = await _fetch_items(category, price_max, limit=limit)

    products: List[Product] = []
    for item in items:
        p = _map_to_product(item)
        if not p:
            continue
        if price_max is not None and p.price > price_max:
            continue
        products.append(p)

    return products


def search_products(message: str, limit: int = 8) -> List[Product]:
    try:
        return asyncio.get_event_loop().run_until_complete(search_products_async(message, limit))
    except RuntimeError:
        # if no running loop
        return asyncio.run(search_products_async(message, limit))
