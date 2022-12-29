import utils.time_converter
from api_client.value_object import MatchInfo
from utils.patch import Patch


class MatchValidator:
    def get_valid_start_end_timestamp(
        start_date: str, end_date: str, format: str, timezone_offset: float
    ) -> tuple:
        patch_start_timestamp = Patch.get_current_patch_start_timestamp()
        if start_date:
            start_timestamp = utils.time_converter.utc_time_to_timestamp(
                start_date, format, timezone_offset
            )
            if start_timestamp < patch_start_timestamp:
                start_timestamp = patch_start_timestamp
        else:
            start_timestamp = patch_start_timestamp
        end_timestamp = (
            utils.time_converter.utc_time_to_timestamp(
                end_date, format, timezone_offset
            )
            if end_date
            else None
        )
        return start_timestamp, end_timestamp

    def has_proper_win_lose(win: int, lose: int) -> bool:
        MIN_COUNT = 30
        if win + lose < MIN_COUNT:
            return False
        MIN_WIN_RATE = 0.4
        MAX_WIN_RATE = 0.6
        win_rate = win / (win + lose)
        return win_rate >= MIN_WIN_RATE and win_rate <= MAX_WIN_RATE

    def is_abnormal_match_info(match_info: MatchInfo) -> bool:
        # 조기종료
        MIN_LENGTH = 20 * 60
        if match_info.duration <= MIN_LENGTH:
            return True
        # Troll
        for participant_info in match_info.participants:
            if participant_info["goldSpent"] <= 2500 and not participant_info["win"]:
                return True
            if participant_info["championName"] == "Yuumi":
                if participant_info["teamPosition"] != "UTILITY":
                    return True
            SMITE_ID = 11
            if participant_info["teamPosition"] == "JUNGLE":
                if (
                    participant_info["summoner1Id"] != SMITE_ID
                    and participant_info["summoner2Id"] != SMITE_ID
                ):
                    return True
                if (
                    participant_info["totalMinionsKilled"]
                    > participant_info["neutralMinionsKilled"]
                ):
                    return True
            else:
                if (
                    participant_info["summoner1Id"] == SMITE_ID
                    or participant_info["summoner2Id"] == SMITE_ID
                ):
                    return True
                if (
                    participant_info["totalMinionsKilled"]
                    < participant_info["neutralMinionsKilled"]
                ):
                    return True
            death_per_minute = participant_info["deaths"] / (match_info.duration / 60)
            if death_per_minute >= 0.5:
                return True
        return False
