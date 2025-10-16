from __future__ import annotations

from typing import Literal

Intent = Literal["product_search", "recommendation", "food_pairing", "general_knowledge"]


def classify_intent(message: str) -> Intent:
    """Very simple rule-based classifier as a starting point.

    This is a placeholder; will be replaced by a more robust approach
    (zero-shot or small classifier) once the basic flow is working.
    """
    text = message.lower()

    # Food pairing
    if "pairs with" in text or "pair with" in text or ("pair" in text and "with" in text):
        return "food_pairing"

    # Recommendation phrasing
    if any(k in text for k in ["recommend", "suggest", "what's good", "whats good", "gift"]):
        return "recommendation"

    # Product search cues: category or constraints
    if any(k in text for k in [
        "show me",
        "find",
        "under",
        "in stock",
        "bourbon",
        "wine",
        "beer",
        "scotch",
        "tequila",
        "whiskey",
        "whisky",
        "vodka",
        "rum",
    ]):
        return "product_search"

    return "general_knowledge"
