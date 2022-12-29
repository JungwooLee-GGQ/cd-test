from __future__ import annotations
import os

from api_client.riot_api_client import RiotAPIClient


class DirectRiotAPIClient(RiotAPIClient):
    def __init__(self, platform: str, api_key: str = None):
        super().__init__(platform)
        self.API_KEY = api_key or os.getenv("RIOT_API_KEY")

    def add_authorization_to_params(self, query_params, body_params, headers) -> tuple:
        api_key = {"X-Riot-Token": self.API_KEY}
        if headers:
            headers.update(api_key)
        else:
            headers = api_key
        return query_params, body_params, headers

    @property
    def platform_api(self):
        return f"https://{self._platform.lower()}.api.riotgames.com/lol"

    @property
    def region_api(self):
        return f"https://{self.region.lower()}.api.riotgames.com/lol"
