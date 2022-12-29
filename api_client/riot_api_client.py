from __future__ import annotations

import logging
from abc import abstractmethod

import requests

from api_client.api_client import APIClient
from api_client.value_object import MatchInfo, SummonerInfo

logger = logging.getLogger(__name__)


class RiotAPIClient(APIClient):
    """The abstract class for a client accesing Riot API.
    Its subclass would access Riot API directly or GGQ Internal gateway server.
    """

    PLATFORM_REGION_MAP = {
        "NA1": "AMERICAS",
        "BR1": "AMERICAS",
        "LA1": "AMERICAS",  # North
        "LA2": "AMERICAS",  # South
        "KR": "ASIA",
        "JP1": "ASIA",
        "EUW1": "EUROPE",
        "EUN1": "EUROPE",
        "TR1": "EUROPE",
        "RU": "EUROPE",
        "OC1": "SEA",
    }
    SOLO_RANK_QUEUE = "RANKED_SOLO_5x5"

    def __init__(self, platform: str):
        self._platform = self._validate_platform(platform)
        self.region = self.PLATFORM_REGION_MAP[self._platform]

    @property
    def platform(self) -> str:
        return self._platform

    @platform.setter
    def platform(self, new_value: str):
        self._platform = self._validate_platform(new_value)
        self.region = self.PLATFORM_REGION_MAP[self._platform]

    @property
    @abstractmethod
    def platform_api(self):
        pass

    @property
    @abstractmethod
    def region_api(self):
        pass

    @classmethod
    def _validate_platform(cls, platform: str) -> str:
        if not isinstance(platform, str):
            raise TypeError(f"platform is not str type")
        upper_platform = platform.upper()
        if upper_platform not in cls.PLATFORM_REGION_MAP:
            raise ValueError(f"Invalid Platform {platform}")
        return upper_platform

    def _validate_match_id(self, match_id: str) -> str:
        # convert the style of match ID with API style using underscore
        upper_id = match_id.upper().replace("-", "_")
        if not upper_id.startswith(self._platform):
            raise ValueError(f"match ID {match_id} has a different platform")
        return upper_id

    ### Wrapper methods for getting and simplifying API response
    @abstractmethod
    def get_recent_game_list(
        self,
        puuid: str,
        count: int = None,
        skip: int = None,
        start_timestamp: int = None,
        end_timestamp: int = None,
    ):
        pass

    def get_summoner_info_by_puuid(
        cls, puuid: str, update_criteria: float = -1
    ) -> SummonerInfo:
        """Get summoner data currently saved in GGQ server,
        if it doest not exists or is outdated(before 'update_criteria' unix timestamp),
        update and get it"""
        raise NotImplementedError

    def get_puuid_by_summoner_id(self, summoner_id: str) -> str:
        uri = self._api_get_a_summoner_by_summoner_id(summoner_id)
        try:
            return self.get_request(uri).json()["puuid"]
        except Exception as e:
            logger.warning(e, exc_info=True)
            return None

    def get_match_data(self, match_id: str) -> MatchInfo:
        match_id = self._validate_match_id(match_id)
        uri = self._api_get_a_match_by_match_id(match_id)
        try:
            match_json = self.get_request(uri).json()["info"]
        except Exception as e:
            logger.info(f"Error on getting '{uri}'")
            logger.info(e, exc_info=True)
            raise requests.HTTPError()
        return MatchInfo(
            match_json.get("gameId", 0),
            match_json.get("gameVersion", ""),
            match_json.get("gameCreation", -1),
            match_json.get("gameDuration", 0),
            match_json.get("gameEndTimestamp", -1),
            match_json.get("participants", []),
        )

    def get_match_timeline(self, match_id: str) -> dict:
        match_id = self._validate_match_id(match_id)
        uri = self._api_get_a_match_timeline_by_match_id(match_id)
        return requests.get(uri).json()["info"]["frames"]

    def get_summoners_in_tier(self, tier, division, page: int = 1) -> list:
        """Get summoner list for a given tier including master, grandmaster, challenger"""
        if tier == "MASTER":
            uri = self._api_get_master_league_for_given_queue(self.SOLO_RANK_QUEUE)
        elif tier == "GRANDMASTER":
            uri = self._api_get_grandmaster_league_for_given_queue(self.SOLO_RANK_QUEUE)
        elif tier == "CHALLENGER":
            uri = self._api_get_challenger_league_for_given_queue(self.SOLO_RANK_QUEUE)
        else:
            uri = self._api_get_league_entries(
                self.SOLO_RANK_QUEUE, tier, division, page
            )
            return self.get_request(uri).json()

        # 'tier' key is not included in each entries in Master, Grandmaster, Challenger tier
        entries = self.get_request(uri).json()["entries"]
        for entry in entries:
            entry["tier"] = tier
        return entries

    def get_champion_mastery_by_suid(self, summoner_id: str) -> list[dict]:
        uri = self._api_get_champion_mastery_by_summoner_id(summoner_id)
        return self.get_request(uri).json()

    ### Riot API Endpoints
    ## CHAMPION-MASTERTY-V4
    def _api_get_champion_mastery_by_summoner_id(self, summoner_id: str) -> list[dict]:
        return f"{self.platform_api}/champion-mastery/v4/champion-masteries/by-summoner/{summoner_id}"

    ## LEAGUE-V4
    def _api_get_master_league_for_given_queue(self, queue: str) -> str:
        return f"{self.platform_api}/league/v4/masterleagues/by-queue/{queue}"

    def _api_get_grandmaster_league_for_given_queue(self, queue: str) -> str:
        return f"{self.platform_api}/league/v4/grandmasterleagues/by-queue/{queue}"

    def _api_get_challenger_league_for_given_queue(self, queue: str) -> str:
        return f"{self.platform_api}/league/v4/challengerleagues/by-queue/{queue}"

    def _api_get_league_entries(
        self, queue: str, tier: str, division: str, page: int = 1
    ) -> str:
        return f"{self.platform_api}/league/v4/entries/{queue}/{tier}/{division}?page={page}"

    ## MATCH-V5
    def _api_get_a_list_of_match_ids_by_puuid(self, puuid: str) -> str:
        return f"{self.region_api}/match/v5/matches/by-puuid/{puuid}/ids"

    def _api_get_a_match_by_match_id(self, match_id: str) -> str:
        return f"{self.region_api}/match/v5/matches/{match_id}"

    def _api_get_a_match_timeline_by_match_id(self, match_id: str) -> str:
        return f"{self.region_api}/match/v5/matches/{match_id}/timeline"

    ## SUMMONER-V4
    def _api_get_a_summoner_by_summoner_id(self, summoner_id: str) -> str:
        return f"{self.platform_api}/summoner/v4/summoners/{summoner_id}"

    def _api_get_a_summoner_by_summoner_name(self, summoner_name: str) -> str:
        return f"{self.platform_api}/summoner/v4/summoners/by-name/{summoner_name}"

    def _api_get_a_summoner_by_puuid(self, puuid: str) -> str:
        return f"{self.platform_api}/summoner/v4/summoners/by-puuid/{puuid}"
