from __future__ import annotations
from api_client.internal_riot_api_client import InternalRiotAPIClient
from app.core.config import settings

APIAccess = InternalRiotAPIClient(settings.PLATFORM)
