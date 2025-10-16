from __future__ import annotations

from typing import List

from ..schemas import Product
from .guardrails import guardrails


def generate_response(message: str, products: List[Product], session_id: str, intent: str) -> str:
    if guardrails.is_intoxication_signaled(message):
        return (
            "I can't assist with orders right now. Please consider checking back later and "
            "drink responsibly."
        )

    if intent == "product_search":
        if products:
            lines = [f"{p.name} (${p.price:.2f}) - SKU {p.sku}" for p in products]
            return "I found these in-stock options:\n" + "\n".join(lines)
        return (
            "I didn't find matching in-stock items yet. Tell me the category and budget, "
            "and I'll search."
        )

    if intent == "food_pairing":
        return (
            "Great choice. Salmon pairs well with Pinot Noir, Chardonnay, or dry Rosé. "
            "Want me to check what's in stock?"
        )

    if intent == "recommendation":
        return (
            "Tell me your budget and flavor preferences (e.g., 'fruity', 'oaky', 'smoky'), "
            "and I'll recommend in-stock options."
        )

    # general_knowledge fallback
    return (
        "Single malt comes from one distillery using malted barley; blended combines whiskies "
        "from multiple distilleries for balance. Want product suggestions?"
    )
