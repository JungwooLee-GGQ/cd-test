from pydantic import BaseSettings


class Settings(BaseSettings):
    API_V1_PREFIX: str = "/gathering/v1"
    SERVER_NAME: str = "Match Gathering Server"
    PLATFORM: str = "KR"


settings = Settings()
