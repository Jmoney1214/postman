from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Product(BaseModel):
    sku: str
    name: str
    category: Optional[str] = None
    price: float
    qty_on_hand: int = 0
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    message: str
    session_id: str


class ChatResponse(BaseModel):
    reply: str
    products: List[Product] = Field(default_factory=list)


class AgeVerifyRequest(BaseModel):
    session_id: str
    dob_iso: str  # YYYY-MM-DD


class AgeVerifyResponse(BaseModel):
    ok: bool
