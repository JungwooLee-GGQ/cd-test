from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.SERVER_NAME, openapi_url=f"{settings.API_V1_PREFIX}/openapi.json"
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)
