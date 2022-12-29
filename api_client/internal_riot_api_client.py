import logging

from api_client.riot_api_client import RiotAPIClient
from api_client.utils import utc_time_to_timestamp
from api_client.value_object import SummonerInfo
from app.core.log_config import log_config

log_config()
logger = logging.getLogger(__name__)


class InternalRiotAPIClient(RiotAPIClient):
    def __init__(self, platform: str):
        super().__init__(platform)
        self._set_server_address(self._platform)

    @RiotAPIClient.platform.setter
    def platform(self, new_value: str):
        super(InternalRiotAPIClient, type(self)).platform.fset(self, new_value)
        self._set_server_address(self._platform)

    def _set_server_address(self, platform: str):
        if self._platform == "KR":
            # PRD
            HOST_URL = "https://lol.api.ggq.gg"
            self.GATEWAY_SERVER = f"{HOST_URL}/gateway/v2/lol"
            self.GATEWAY_SERVER_WITH_PLATFORM = (
                f"{HOST_URL}/gateway/v2/{self._platform}/lol"
            )
            self.APPLICATION_SERVER = f"{HOST_URL}/application/v1"
        elif self._platform == "EUW1":
            # STG
            HOST_URL = (
                "http://alb-ew1-s-pub-ggq-lol-2122255726.eu-west-1.elb.amazonaws.com"
            )
            self.GATEWAY_SERVER = f"{HOST_URL}/gateway/v2/lol"
            self.GATEWAY_SERVER_WITH_PLATFORM = (
                f"{HOST_URL}/gateway/v2/{self._platform}/lol"
            )
            self.APPLICATION_SERVER = f"{HOST_URL}/application/v1"
        else:
            raise ValueError(f"Not support for '{platform}'")

    @property
    def platform_api(self):
        return self.GATEWAY_SERVER_WITH_PLATFORM

    @property
    def region_api(self):
        return self.GATEWAY_SERVER

    @classmethod
    def _filter_rank_info(cls, ranks: list[dict], rank_type: str = "RANKED_SOLO_5x5"):
        return next(filter(lambda x: x.get("type") == rank_type, ranks), None)

    @classmethod
    def _convert_json_to_summoner_info(cls, json_data: dict) -> SummonerInfo:
        # for json_data returned from application server
        puuid = json_data.get("puuid", "")
        summoner_id = json_data.get("summonerId", "")
        name = json_data.get("name", "")
        rank = json_data.get("ranks", [])
        solo_rank_info = cls._filter_rank_info(rank)
        if solo_rank_info:
            timestamp = utc_time_to_timestamp(solo_rank_info["writtenTime"])
            return SummonerInfo(
                puuid=puuid,
                summoner_id=summoner_id,
                name=name,
                tier=solo_rank_info["tier"],
                division=solo_rank_info["division"],
                lp=solo_rank_info["leaguePoint"],
                win=solo_rank_info["win"],
                lose=solo_rank_info["lose"],
                written_timestamp=timestamp,
            )
        return SummonerInfo(puuid, summoner_id, name)

    def get_recent_game_list(
        self,
        puuid: str,
        count: int = None,
        skip: int = None,
        start_timestamp: int = None,
        end_timestamp: int = None,
    ) -> list[str]:
        uri = f"{self.APPLICATION_SERVER}/summoners/{puuid}/match-ids"
        # uri = f"{self.GATEWAY_SERVER}/match/v5/matches/by-puuid/{puuid}/ids"
        SOLO_RANK_ID = 420
        params = {"queue": SOLO_RANK_ID}
        if skip is not None:
            params["start"] = skip
        if count is not None:
            params["count"] = count
        if start_timestamp is not None:
            params["startTime"] = start_timestamp
        if end_timestamp is not None:
            params["endTime"] = end_timestamp
        return self.get_request(uri, query=params).json()

    def get_summoner_data_by_puuid(
        self, puuid: str, update_criteria: float = -1
    ) -> dict:
        """Get summoner data currently saved in GGQ server,
        if it doest not exists or is outdated(before 'update_criteria' in unix timestamp),
        update and get it"""
        # uri = f"{self.APPLICATION_SERVER}/summoners/{puuid}"
        # update_uri = f"{self.GATEWAY_SERVER_WITH_PLATFORM}/summoner/v4/summoners/by-puuid/{puuid}"
        # response = self.get_request(uri)
        # if response.status_code == 200:
        #     data = response.json()
        #     ranks = data.get("ranks", [])
        #     if len(ranks) == 0:  # rank info has not been searched
        #         response = self.get_request(update_uri)
        #         data = response.json()
        #         return data
        #     if update_criteria < 0:
        #         return data
        #     solo_rank_info = self._filter_rank_info(ranks)
        #     if solo_rank_info:
        #         written_time = solo_rank_info.get("writtenTime", 0)
        #         written_timestamp = utc_time_to_timestamp(written_time)
        #         if written_timestamp >= update_criteria:
        #             return data
        # response = self.get_request(update_uri)
        # data = response.json()
        # return data

        uri = f"{self.APPLICATION_SERVER}/summoners/{puuid}"
        get_request = self.get_request(uri)
        if get_request.status_code == 200:
            data = get_request.json()
            ranks = data.get("ranks", [])
            if len(ranks) == 0:  # rank info has not been searched
                return self.post_request(uri).json()
            if update_criteria < 0:
                return data
            solo_rank_info = self._filter_rank_info(ranks)
            if solo_rank_info:
                written_time = solo_rank_info.get("writtenTime", 0)
                written_timestamp = utc_time_to_timestamp(written_time)
                if written_timestamp >= update_criteria:
                    return data
        return self.post_request(uri).json()

    def get_summoner_info_by_puuid(
        self, puuid: str, update_criteria: float = -1
    ) -> SummonerInfo:
        return self._convert_json_to_summoner_info(
            self.get_summoner_data_by_puuid(puuid, update_criteria)
        )
