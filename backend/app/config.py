from __future__ import annotations

import os
from pydantic import BaseModel


class Settings(BaseModel):
    lightspeed_api_key: str | None = os.getenv("LIGHTSPEED_API_KEY")
    lightspeed_account_id: str | None = os.getenv("LIGHTSPEED_ACCOUNT_ID")
    environment: str = os.getenv("ENVIRONMENT", "development")


settings = Settings()