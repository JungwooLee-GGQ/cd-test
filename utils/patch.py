import time
import utils.time_converter


class Patch:
    PATCH_DATE = {
        "12.2": "2022-01-20",
        "12.3": "2022-02-02",
        "12.4": "2022-02-16",
        "12.5": "2022-03-02",
        "12.6": "2022-03-30",
        "12.7": "2022-04-13",
        "12.8": "2022-04-27",
        "12.9": "2022-05-11",
        "12.10": "2022-05-25",
        "12.11": "2022-06-08",
        "12.12": "2022-06-23",
        "12.13": "2022-07-13",
        "12.14": "2022-07-27",
        "12.15": "2022-08-10",
        "12.16": "2022-08-24",
        "12.17": "2022-09-08",
        "12.18": "2022-09-21",
        "12.19": "2022-10-05",
        "12.20": "2022-10-19",
        "12.21": "2022-11-02",
        "12.22": "2022-11-16",
        "12.23": "2022-12-07",
    }

    @classmethod
    def get_current_version(
        cls, format: str = "%Y-%m-%d %H:%M", timezone_offset: float = 9
    ):
        current_time = time.time()
        current_patch = None
        for patch, patch_date_str in cls.PATCH_DATE.items():
            # patch starts at 06:00, give extra 30 mins
            patch_timestamp = utils.time_converter.utc_time_to_timestamp(
                f"{patch_date_str} 06:30", format, timezone_offset
            )
            if current_time > patch_timestamp:
                current_patch = patch
        return current_patch

    @classmethod
    def get_current_patch_start_timestamp(cls) -> int:
        return cls.get_patch_start_timestamp(cls.get_current_version())

    @classmethod
    def get_patch_start_timestamp(
        cls, patch: str, format: str = "%Y-%m-%d %H:%M", timezone_offset: float = 9
    ) -> int:
        if patch not in cls.PATCH_DATE:
            return -1
        patch_date = cls.PATCH_DATE[patch]
        return utils.time_converter.utc_time_to_timestamp(
            f"{patch_date} 06:30", format, timezone_offset
        )
