import json
import os
import unittest
from app.validator.match_validator import MatchValidator
from api_client.value_object import MatchInfo


class MatchValidatorTest(unittest.TestCase):
    def test_when_start_and_end_date_given_then_return_valid_timestamp_tuple(self):
        self.assertEqual(
            MatchValidator.get_valid_start_end_timestamp(
                start_date="2022-11-16",
                end_date="2022-11-29",
                format="%Y-%m-%d",
                timezone_offset=9,
            ),
            (1668547800.0, 1669647600.0),  # 11-16, 11-29
        )

    def test_when_games_under_minimun_given_return_false(self):
        self.assertEqual(MatchValidator.has_proper_win_lose(10, 10), False)
        self.assertEqual(MatchValidator.has_proper_win_lose(10, 20), False)
        self.assertEqual(MatchValidator.has_proper_win_lose(20, 10), False)

    def test_when_negative_value_given_return_false(self):
        self.assertEqual(MatchValidator.has_proper_win_lose(60, -1), False)
        self.assertEqual(MatchValidator.has_proper_win_lose(-1, 40), False)
        self.assertEqual(MatchValidator.has_proper_win_lose(-59, -41), False)

    def test_when_user_win_rate_invalid_given_return_false(self):
        self.assertEqual(MatchValidator.has_proper_win_lose(70, 30), False)
        self.assertEqual(MatchValidator.has_proper_win_lose(30, 70), False)
        self.assertEqual(MatchValidator.has_proper_win_lose(0, 100), False)
        self.assertEqual(MatchValidator.has_proper_win_lose(100, 0), False)

    def test_when_valid_user_data_given_return_true(self):
        self.assertEqual(MatchValidator.has_proper_win_lose(40, 60), True)
        self.assertEqual(MatchValidator.has_proper_win_lose(50, 50), True)
        self.assertEqual(MatchValidator.has_proper_win_lose(60, 40), True)

    def test_when_abnormal_match_data_given_then_return_true(self):
        with open(
            os.path.join("test", "data", "match_detail_KR_5889814856.json"),
            "r",
            encoding="utf-8",
        ) as f:
            wrong_match_detail = json.load(f)["info"]
            match_info = MatchInfo(
                wrong_match_detail["gameId"],
                wrong_match_detail["gameVersion"],
                wrong_match_detail["gameCreation"],
                wrong_match_detail["gameDuration"],
                wrong_match_detail["gameEndTimestamp"],
                wrong_match_detail["participants"],
            )
            # when yuumi is in MIDDLE and has SMITE
            self.assertTrue(
                MatchValidator.is_abnormal_match_info(match_info=match_info)
            )
            match_info.participants[7]["championName"] = "Ahri"
            # when Ahri has SMITE
            self.assertTrue(MatchValidator.is_abnormal_match_info(match_info))
            # when abnormal property is removed
            match_info.participants[7]["summoner1Id"] = 12
            self.assertFalse(MatchValidator.is_abnormal_match_info(match_info))
