from __future__ import annotations

import collections
import heapq
import logging
import os

from tqdm import tqdm

import utils
import utils.time_converter
from api_client.riot_api_client import SummonerInfo
from app import APIAccess
from app.collector.tier_group import TierGroup
from app.core.log_config import log_config
from app.validator.match_validator import MatchValidator

log_config()
logger = logging.getLogger(__name__)


class MatchSampler:
    MAX_GAME_PER_USER = 3

    def __init__(
        self,
        tier_group: TierGroup,
        version: str,
        save_file_directory: str,
        user_dict: dict[str, SummonerInfo],
        user_validity: dict[str, bool],
        timezone_offset: float = 9,
    ):
        self.version = version
        self.user_dict = user_dict
        self.user_validity = user_validity
        self.tier_group = tier_group
        self.match_output = os.path.join(
            save_file_directory, f"{tier_group.name}_match_list.txt"
        )
        self.invalid_match_output = os.path.join(
            save_file_directory, f"{tier_group.name}_invalid_match_list.txt"
        )
        self.timezone_offset = timezone_offset
        self.save_file_directory = save_file_directory
        # to not download duplicate match
        self._initialize_match_list()

    def _initialize_match_list(self):
        self.matches_collected = set()
        self.invalid_matches = set()
        if os.path.exists(self.match_output):
            with open(self.match_output, "r") as f:
                match_list = f.read().splitlines()
                for match in match_list:
                    self.matches_collected.add(match)
        if os.path.exists(self.invalid_match_output):
            with open(self.invalid_match_output, "r") as f:
                match_list = f.read().splitlines()
                for match in match_list:
                    self.invalid_matches.add(match)

    def match_sampling(
        self,
        count_to_collect: int,
        start_timestamp: int,
        end_timestamp: int,
        users_to_search: list,
        user_record: dict,
        days: int,
        format: str,
    ) -> None:
        total_count = count_to_collect * days + len(self.matches_collected)
        with tqdm(
            total=count_to_collect * days,
            desc=f"{self.tier_group.name} : match to collect",
        ) as match_progress_bar:
            abnormal_match_count = 0
            collect_per_day = 0
            while users_to_search and len(self.matches_collected) < total_count:
                user_to_search = heapq.heappop(users_to_search)[1]
                GAME_COUNT = 50
                if collect_per_day >= count_to_collect:
                    start_date = utils.time_converter.add_day_from_timestamp(
                        start_timestamp, 1, format, self.timezone_offset
                    )
                    end_date = utils.time_converter.add_day_from_timestamp(
                        end_timestamp, 2, format, self.timezone_offset
                    )
                    start_timestamp = utils.time_converter.utc_time_to_timestamp(
                        start_date, format, self.timezone_offset
                    )
                    end_timestamp = utils.time_converter.utc_time_to_timestamp(
                        end_date, format, self.timezone_offset
                    )
                    collect_per_day = 0
                recent_games = self.get_recent_games(
                    user_to_search, GAME_COUNT, 0, start_timestamp, end_timestamp
                )
                game_per_user = 0
                for match_id in recent_games:
                    if collect_per_day >= count_to_collect:
                        break
                    if game_per_user >= self.MAX_GAME_PER_USER:
                        break
                    if (
                        match_id in self.matches_collected
                        or match_id in self.invalid_matches
                    ):
                        continue
                    try:
                        match_data = APIAccess.get_match_data(match_id)
                    except:
                        continue
                    if not match_data.version.startswith(self.version):
                        break
                    if MatchValidator.is_abnormal_match_info(match_data):
                        self.invalid_matches.add(match_id)
                        abnormal_match_count += 1
                        continue

                    participants_puuid = match_data.participants_puuid
                    if "BOT" in participants_puuid:
                        logger.warning(
                            f"wrong puuid: {participants_puuid} in match '{match_id}'"
                        )
                        continue
                    if len(participants_puuid) < 10:
                        logger.info(f"Not valid number of members: {match_id}")
                        continue

                    not_recorded_puuids = [
                        p for p in participants_puuid if p not in self.user_dict
                    ]

                    def update_result(result):
                        puuid, valid = result
                        if valid:
                            heapq.heappush(users_to_search, (0, puuid))
                            user_record[puuid] = 0

                    # for puuid in not_recorded_puuids:
                    #     update_result(self.check_participant(puuid))
                    utils.run_multithread(
                        self.check_participant, not_recorded_puuids, update_result
                    )

                    if self.is_match_qualified(participants_puuid):
                        match_progress_bar.update(1)
                        self.matches_collected.add(match_id)
                        game_per_user += 1
                        collect_per_day += 1
                        user_record[user_to_search] += 1
                        utils.write_text(self.match_output, match_id + "\n", "a")
                        if len(self.matches_collected) >= total_count:
                            break
                    else:
                        self.invalid_matches.add(match_id)
                        utils.write_text(
                            self.invalid_match_output, match_id + "\n", "a"
                        )
        return user_record

    def is_match_qualified(
        self,
        participants_puuid,
    ):
        win_rates = [
            self.user_validity[p] for p in participants_puuid if p in self.user_validity
        ]
        win_result = [
            (self.user_dict[p].win, self.user_dict[p].lose) for p in participants_puuid
        ]
        is_win_rate_valid = all(win_rates)
        if not is_win_rate_valid:
            logger.debug(f"win rate not valid: {win_rates}, {win_result}")

        rank_numbers = sorted(
            [self.user_dict[p].rank_number for p in participants_puuid]
        )
        is_all_in_group = all(
            filter(
                lambda x: self.tier_group.is_adjacent_rank(x),
                rank_numbers,
            )
        )
        is_median_in_group = (
            TierGroup.get_from_rank_number(rank_numbers[4]) == self.tier_group
            and TierGroup.get_from_rank_number(rank_numbers[5]) == self.tier_group
        )
        return is_win_rate_valid and is_all_in_group and is_median_in_group

    def check_participant(
        self,
        puuid: str,
    ):
        summoner_info = APIAccess.get_summoner_info_by_puuid(puuid)
        self.user_dict[puuid] = summoner_info  # puuid is not checked
        win_validity = MatchValidator.has_proper_win_lose(
            summoner_info.win, summoner_info.lose
        )
        self.user_validity[puuid] = win_validity
        do_search = win_validity and summoner_info.tier_group == self.tier_group
        return puuid, do_search

    @classmethod
    def get_recent_games(
        cls,
        puuid: str,
        count: int,
        skip: int = 0,
        start_time: int = None,
        end_time: int = None,
    ) -> list[str]:
        result = APIAccess.get_recent_game_list(
            puuid=puuid,
            skip=skip,
            count=count,
            start_timestamp=start_time,
            end_timestamp=end_time,
        )
        return result.get("matchIds", [])
        # return result

    def _collect_all_matches(
        self,
        start_timestamp: int,
        end_timestamp: int,
        users_to_search: collections.deque,
    ):
        MATCH_COUNT_MAX = 100
        abnormal_match_count = 0
        for puuid in users_to_search:
            do = True
            start_index = 0
            while do:
                match_list = self.get_recent_games(
                    puuid=puuid,
                    skip=start_index,
                    count=MATCH_COUNT_MAX,
                    start_time=start_timestamp,
                    end_time=end_timestamp,
                )
                do = len(match_list) == MATCH_COUNT_MAX
                start_index += MATCH_COUNT_MAX

                for match_id in match_list:
                    if (
                        match_id in self.invalid_matches
                        or match_id in self.matches_collected
                    ):
                        continue
                    match_data = APIAccess.get_match_data(match_id)
                    if MatchValidator.is_abnormal_match_info(match_data):
                        self.invalid_matches.add(match_id)
                        utils.write_text(
                            self.invalid_match_output, match_id + "\n", "a"
                        )
                        abnormal_match_count += 1
                        continue
                    self.matches_collected.add(match_id)
                    utils.write_text(self.match_output, match_id + "\n", "a")
