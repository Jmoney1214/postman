from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .schemas import ChatRequest, ChatResponse, AgeVerifyRequest, AgeVerifyResponse
from .services.intent import classify_intent
from .services.lightspeed_client import search_products
from .services.chat_response import generate_response
from .services.guardrails import guardrails


app = FastAPI(title="Liquor Store AI Assistant API", version="0.1.0")

# Allow embedding in various sites during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    # Enforce age verification for any product-related intent
    intent = classify_intent(request.message)
    products = []
    if intent in ("product_search", "recommendation"):
        if not guardrails.is_verified(request.session_id):
            raise HTTPException(status_code=403, detail="Age verification required.")
        products = search_products(request.message)

    reply = generate_response(request.message, products, request.session_id, intent)
    return ChatResponse(reply=reply, products=products)


@app.post("/age/verify", response_model=AgeVerifyResponse)
async def age_verify(payload: AgeVerifyRequest) -> AgeVerifyResponse:
    ok = guardrails.verify_age(payload.session_id, payload.dob_iso)
    return AgeVerifyResponse(ok=ok)
