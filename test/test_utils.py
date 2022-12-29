import unittest
import utils.time_converter
import utils.patch
import utils
from app.collector.tier_group import TierGroup
import time


class UtilsInitTest(unittest.TestCase):
    def test_when_valid_data_given_then_return_valid_rank_number(self):
        self.assertEqual(utils.rank_to_number("CHALLENGER", "I"), 27)
        self.assertEqual(utils.rank_to_number("GRANDMASTER", "I"), 26)
        self.assertEqual(utils.rank_to_number("MASTER", "I"), 25)
        self.assertEqual(utils.rank_to_number("GOLD", "I"), 16)
        self.assertEqual(utils.rank_to_number("GOLD", "II"), 15)
        self.assertEqual(utils.rank_to_number("GOLD", "III"), 14)
        self.assertEqual(utils.rank_to_number("GOLD", "IV"), 13)


class TierGroupTest(unittest.TestCase):
    def test_when_input_valid_data_given_then_return_valid_rank(self):
        self.assertEqual(TierGroup.get_from_rank_number(0), TierGroup.U)
        self.assertEqual(TierGroup.get_from_rank_number(10), TierGroup.S34)
        self.assertEqual(TierGroup.get_from_rank_number(9), TierGroup.S34)
        self.assertEqual(TierGroup.get_from_rank_number(27), TierGroup.C1)
        self.assertEqual(TierGroup.get_from_rank_number(26), TierGroup.GM1)

    def test_when_input_invalid_data_given_then_return_unrank(self):
        self.assertEqual(TierGroup.get_from_rank_number(-3), TierGroup.U)
        self.assertEqual(TierGroup.get_from_rank_number(28), TierGroup.U)

    def test_when_unrank_given_then_return_false(self):
        self.assertEqual(TierGroup.is_adjacent_rank(TierGroup.I34, 0), False)

    def test_when_away_two_rank_given_then_return_false(self):
        self.assertEqual(TierGroup.is_adjacent_rank(TierGroup.I34, 4), False)
        self.assertEqual(TierGroup.is_adjacent_rank(TierGroup.I34, 28), False)
        self.assertEqual(TierGroup.is_adjacent_rank(TierGroup.C1, 2), False)
        self.assertEqual(TierGroup.is_adjacent_rank(TierGroup.C1, 30), False)

    def test_when_adjacent_two_rank_given_then_return_true(self):
        self.assertEqual(TierGroup.is_adjacent_rank(TierGroup.I34, 2), True)
        self.assertEqual(TierGroup.is_adjacent_rank(TierGroup.C1, 25), True)


class TimeTests(unittest.TestCase):
    def test_when_format_given_then_time_convert_to_timestamp_works(self):
        local_time_difference = time.mktime(time.localtime()) - time.mktime(
            time.gmtime()
        )
        # then local time conversion works
        self.assertEqual(
            utils.time_converter.local_time_to_timestamp("2022-07-28 03:19")
            + local_time_difference,
            1658978340,
        )

        # when decimal points is not given in time_string
        # then utc time conversion works
        self.assertEqual(
            utils.time_converter.utc_time_to_timestamp("2022-07-28T03:19:00Z"),
            1658978340,
        )
        self.assertEqual(
            utils.time_converter.utc_time_to_timestamp("1970-01-01T00:00:00Z"), 0
        )
        self.assertEqual(
            utils.time_converter.utc_time_to_timestamp("1969-12-31T23:59:00Z"), -60
        )
        # when decimal points is given in time_string
        # then utc time conversion works
        self.assertEqual(
            utils.time_converter.utc_time_to_timestamp("2022-07-28T03:19:00.50Z"),
            1658978340.5,
        )
        self.assertEqual(
            utils.time_converter.utc_time_to_timestamp("2022-07-28T03:19:00.500Z"),
            1658978340.5,
        )
        self.assertEqual(
            utils.time_converter.utc_time_to_timestamp("1970-01-01T00:00:00.05Z"), 0.05
        )

        # when timezone offset is set then utc time conversion works
        self.assertEqual(
            utils.time_converter.utc_time_to_timestamp("1970-01-01", "%Y-%m-%d", 0),
            0,
        )
        self.assertEqual(
            utils.time_converter.utc_time_to_timestamp("1970-01-01", "%Y-%m-%d", 9),
            -32400,
        )
        self.assertEqual(
            utils.time_converter.utc_time_to_timestamp("1970-01-01", "%Y-%m-%d", -3),
            10800,
        )

    def test_when_no_format_for_time_string_given_then_raise_error(self):
        # when format is not set
        self.assertRaises(
            ValueError,
            utils.time_converter.local_time_to_timestamp,
            "2022-07-28T03:19:00Z",
        )
        self.assertRaises(
            ValueError,
            utils.time_converter.utc_time_to_timestamp,
            "2022-07-28 03:19:00.000",
        )
        # when format is set
        self.assertRaises(
            ValueError,
            utils.time_converter.local_time_to_timestamp,
            "2022-07-28T03:19:00Z",
            "%Y-%m-%dT%H:%M:%S.%fZ",
        )
        self.assertRaises(
            ValueError,
            utils.time_converter.utc_time_to_timestamp,
            "2022-07-28 03:19:00.000",
            "%Y-%m-%d %H:%M:%S",
        )

    def test_when_not_valid_time_string_given_then_raise_error(self):
        self.assertRaises(
            ValueError,
            utils.time_converter.utc_time_to_timestamp,
            "2022-07-32 03:19:00.000",
        )
        self.assertRaises(
            ValueError,
            utils.time_converter.utc_time_to_timestamp,
            "2022-07-32 25:19:00.000",
        )


if __name__ == "__main__":
    unittest.main()
