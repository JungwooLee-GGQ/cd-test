from __future__ import annotations
import collections
import os
import heapq
import utils
import json
import utils.time_converter
from utils.patch import Patch
from api_client.value_object import SummonerInfo
from app.collector.tier_group import TierGroup
from app.sampler.user_sampler import UserSampler
from app.sampler.match_sampler import MatchSampler
from app.validator.match_validator import MatchValidator


class MatchCollector:
    SAVE_FILE_FOLDER = "save_files"

    def __init__(
        self,
        tier_group: TierGroup,
        timezone_offset: float = 9,
        format: str = "%Y-%m-%d",
    ) -> None:
        # default timezone is KST (UTC+9)
        self.version = Patch.get_current_version()
        self.tier_group = tier_group
        self.user_dict: dict[str, SummonerInfo] = {}  # key: puuid
        self.user_validity: dict[str, bool] = {}  # key: puuid
        self.user_record: dict[str, int] = {}  # key: puuid
        self.timezone_offset = timezone_offset
        self.format = format
        self.set_save_file_directory(version=self.version)
        self.user_record_file = os.path.join(
            self.save_file_directory, f"{self.tier_group.name}_user_record.txt"
        )

    def _initialize_user_record(self):
        if not os.path.exists(self.user_record_file):
            return
        with open(self.user_record_file, "r") as f:
            self.user_record: dict = json.load(f)

    def set_save_file_directory(self, version: str):
        self.save_file_directory = os.path.join(
            os.getcwd(), self.SAVE_FILE_FOLDER, version
        )
        os.makedirs(self.save_file_directory, exist_ok=True)

    def collect_tier_match(
        self,
        count_to_collect: int,
        user_count: int = 0,
        is_daily_collect: bool = False,
        renew_sampling: bool = True,
        start_date: str = "",
        end_date: str = "",
    ):
        if is_daily_collect:
            start_date, end_date = utils.time_converter.get_daily_start_end_date(
                self.format
            )
        self.run_collector(
            start_date=start_date,
            end_date=end_date,
            count_to_collect=count_to_collect,
            user_count=user_count,
            renew_sampling=renew_sampling,
        )

    def collect_all_match(
        self,
        is_daily_collect: bool = False,
        renew_sampling: bool = True,
        start_date: str = "",
        end_date: str = "",
    ):
        if is_daily_collect:
            start_date, end_date = utils.time_converter.get_daily_start_end_date(
                self.format
            )

        start_timestamp, end_timestamp = MatchValidator.get_valid_start_end_timestamp(
            start_date, end_date, self.format, self.timezone_offset
        )
        user_sampler = UserSampler(
            tier_group=self.tier_group, save_file_directory=self.save_file_directory
        )
        users_to_search: collections.deque = user_sampler.user_collecting(
            renew_sampling=renew_sampling
        )
        match_sampler = MatchSampler(
            tier_group=self.tier_group,
            version=self.version,
            save_file_directory=self.save_file_directory,
            user_dict=user_sampler.user_dict,
            user_validity=user_sampler.user_validity,
        )
        match_sampler._collect_all_matches(
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            users_to_search=users_to_search,
        )

    def run_collector(
        self,
        start_date: str,
        end_date: str,
        count_to_collect: int,
        user_count: int,
        renew_sampling: bool = True,
    ):
        self._initialize_user_record()
        days = utils.time_converter.get_date_difference(
            start_date=start_date, end_date=end_date, format=self.format
        )
        start_timestamp, end_timestamp = MatchValidator.get_valid_start_end_timestamp(
            start_date, end_date, self.format, self.timezone_offset
        )
        user_sampler = UserSampler(
            tier_group=self.tier_group, save_file_directory=self.save_file_directory
        )
        users_to_search: collections.deque = user_sampler.user_sampling(
            user_count, renew_sampling
        )
        for puuid in users_to_search:
            if puuid not in self.user_record.keys():
                self.user_record[puuid] = 0
        search_list = []
        for puuid, priority in self.user_record.items():
            heapq.heappush(search_list, (priority, puuid))

        match_sampler = MatchSampler(
            tier_group=self.tier_group,
            version=self.version,
            save_file_directory=self.save_file_directory,
            user_dict=user_sampler.user_dict,
            user_validity=user_sampler.user_validity,
        )
        user_record = match_sampler.match_sampling(
            count_to_collect=count_to_collect,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            users_to_search=search_list,
            user_record=self.user_record,
            days=days,
            format=self.format,
        )
        self.update_user_record(user_record)

    def update_user_record(self, user_record: dict):
        with open(self.user_record_file, "w") as f:
            json.dump(user_record, f, separators=(",", ":"))
