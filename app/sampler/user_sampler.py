import collections
import logging
import utils
import json
from app import APIAccess
from api_client.value_object import SummonerInfo
from app.collector.tier_group import TierGroup
from app.validator.match_validator import MatchValidator
from utils.patch import Patch
from app.core.log_config import log_config
import os
import time

log_config()
logger = logging.getLogger(__name__)


class UserSampler:
    def __init__(self, tier_group: TierGroup, save_file_directory: str) -> None:
        self.version = Patch.get_current_version()
        self.user_dict: dict[str, SummonerInfo] = {}  # key: puuid
        self.user_validity: dict[str, bool] = {}  # key: puuid
        self.tier_group = tier_group
        self.is_user_list_initialized = False
        self.is_user_validity_initialized = False

        self.user_list_file = os.path.join(
            save_file_directory, f"{tier_group.name}_user_list.txt"
        )
        self.user_validity_file = os.path.join(
            save_file_directory, f"{tier_group.name}_user_validity.txt"
        )
        self._initialize_user_dict()

    def _initialize_user_dict(self):
        if not os.path.exists(self.user_list_file):
            return
        with open(self.user_list_file, "r") as f:
            json_data = json.load(f)
            self.user_dict = {
                k: SummonerInfo.from_dict(v) for k, v in json_data.items()
            }
        self.is_user_list_initialized = True
        if not os.path.exists(self.user_validity_file):
            return
        with open(self.user_validity_file, "r") as f:
            self.user_validity = json.load(f)
        self.is_user_validity_initialized = True

    def collect_all_user(self) -> collections.deque:
        logger.info(f"ALL '{self.tier_group.name}' USER COLLECTING")
        users_to_search = collections.deque()
        user_list = self.get_tier_group_user_list(self.tier_group)

        utils.run_multithread(self.record_user, user_list)
        users_to_search.extend(self.user_dict.keys())

        with open(self.user_list_file, "w") as f:
            json.dump({k: v.to_dict() for k, v in self.user_dict.items()}, f)
        return users_to_search

    def user_collecting(self, renew_sampling: bool = True) -> collections.deque:
        if not renew_sampling:
            if self.is_user_list_initialized:
                logger.info(f"User input is initialized from {self.user_list_file}")
                users_to_search = collections.deque()
                users_to_search.extend(
                    [puuid for puuid, value in self.user_dict.items() if value]
                )
        else:
            users_to_search = self.collect_all_user()
        return users_to_search

    def user_sampling(
        self, user_count: int = 3260, renew_sampling: bool = True
    ) -> collections.deque:
        if not renew_sampling:
            if self.is_user_validity_initialized:
                logger.info(f"User input is initialized from {self.user_list_file}")
                users_to_search = collections.deque()
                users_to_search.extend(
                    [puuid for puuid, valid in self.user_validity.items() if valid]
                )
                if len(self.user_dict) >= user_count:
                    return users_to_search

        logger.info(f"'{self.tier_group.name}' USER SAMPLING")
        users_to_search = collections.deque()
        user_list = self.get_tier_group_user_list(self.tier_group, user_count)

        def update_result(puuid):
            user = self.user_dict[puuid]
            valid = MatchValidator.has_proper_win_lose(user.win, user.lose)
            self.user_validity[puuid] = valid
            if valid:
                users_to_search.append(puuid)

        utils.run_multithread(
            self.record_user,
            user_list,
            update_result,
            use_tqdm=True,
            tqdm_decs=f"{self.tier_group.name} user to research",
        )
        with open(self.user_list_file, "w") as f:
            json.dump(
                {k: v.to_dict() for k, v in self.user_dict.items()},
                f,
                separators=(",", ":"),
            )
        with open(self.user_validity_file, "w") as f:
            json.dump(self.user_validity, f, separators=(",", ":"))
        return users_to_search

    # 'user' is a dictionary with summoner ID and name, tier, wins, loses
    def record_user(self, user: dict) -> str:
        puuid = APIAccess.get_puuid_by_summoner_id(user["summonerId"])
        self.user_dict[puuid] = SummonerInfo(
            puuid=puuid,
            summoner_id=user["summonerId"],
            name=user["summonerName"],
            tier=user["tier"],
            division=user["rank"],
            lp=user["leaguePoints"],
            win=user["wins"],
            lose=user["losses"],
            written_timestamp=time.time(),
        )
        return puuid

    @classmethod
    def get_both_user_list(
        cls, tier: str, division_1: str, division_2: str, user_count: int
    ):
        half = user_count // 2
        return cls.get_user_list(tier, division_1, half) + cls.get_user_list(
            tier, division_2, user_count - half
        )

    @classmethod
    def get_user_list(cls, tier: str, division: str, user_count: int):
        user_ids = []
        user_list = []
        page = 1
        while len(user_list) < user_count:
            user_info = APIAccess.get_summoners_in_tier(tier, division, page)
            for summoner in user_info:
                if summoner["summonerId"] not in user_ids:
                    user_list.append(summoner)
                    user_ids.append(summoner["summonerId"])
            page += 1
        return user_list[:user_count]

    @classmethod
    def get_tier_group_user_list(
        cls, tier_group: TierGroup, user_count: int = 408
    ) -> list:
        if user_count < 1:
            return []
        if tier_group == TierGroup.C1:
            return APIAccess.get_summoners_in_tier("CHALLENGER", "I")
        elif tier_group == TierGroup.GM1:
            return APIAccess.get_summoners_in_tier("GRANDMASTER", "I")
        elif tier_group == TierGroup.A:
            return APIAccess.get_summoners_in_tier(
                "CHALLENGER", "I"
            ) + APIAccess.get_summoners_in_tier("GRANDMASTER", "I")
        elif tier_group == TierGroup.M1:
            return APIAccess.get_summoners_in_tier("MASTER", "I")
        elif tier_group == TierGroup.D12:
            return cls.get_both_user_list("DIAMOND", "I", "II", user_count)
        elif tier_group == TierGroup.D34:
            return cls.get_both_user_list("DIAMOND", "III", "IV", user_count)
        elif tier_group == TierGroup.P12:
            return cls.get_both_user_list("PLATINUM", "I", "II", user_count)
        elif tier_group == TierGroup.P34:
            return cls.get_both_user_list("PLATINUM", "III", "IV", user_count)
        elif tier_group == TierGroup.G12:
            return cls.get_both_user_list("GOLD", "I", "II", user_count)
        elif tier_group == TierGroup.G34:
            return cls.get_both_user_list("GOLD", "III", "IV", user_count)
        elif tier_group == TierGroup.S12:
            return cls.get_both_user_list("SILVER", "I", "II", user_count)
        elif tier_group == TierGroup.S34:
            return cls.get_both_user_list("SILVER", "III", "IV", user_count)
        elif tier_group == TierGroup.B12:
            return cls.get_both_user_list("BRONZE", "I", "II", user_count)
        elif tier_group == TierGroup.B34:
            return cls.get_both_user_list("BRONZE", "III", "IV", user_count)
        elif tier_group == TierGroup.I12:
            return cls.get_both_user_list("IRON", "I", "II", user_count)
        elif tier_group == TierGroup.I34:
            return cls.get_both_user_list("IRON", "III", "IV", user_count)
        return []
