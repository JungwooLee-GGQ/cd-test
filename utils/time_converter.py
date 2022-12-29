import time
import datetime


def local_time_to_timestamp(time_string: str, format: str = "%Y-%m-%d %H:%M"):
    """Convert time string in local timezone to Unix timestamp

    It may not cover the case when DST(daylight saving time) seasons have changed.
    """
    return time.mktime(time.strptime(time_string, format))


def utc_time_to_timestamp(
    time_string: str, format: str = None, offset: float = 0
) -> float:
    """Convert time string in UTC(GMT, or Zulu time) to Unix timestamp

    The default time format follows ISO 8601 (%Y-%m-%dT%H:%M:%S.%fZ or %Y-%m-%dT%H:%M:%SZ)

    time_string: time string in UTC+0
    format: the format by which time string is written
    offset: change timezone to UTC+{offset}
    """
    if not format:
        if "." in time_string:
            format = "%Y-%m-%dT%H:%M:%S.%fZ"
        else:
            format = "%Y-%m-%dT%H:%M:%SZ"
    return (
        datetime.datetime.strptime(time_string, format)
        .replace(tzinfo=datetime.timezone(datetime.timedelta(hours=offset)))
        .timestamp()
    )


def get_date_difference(start_date: str, end_date: str, format: str) -> int:
    result = datetime.datetime.strptime(end_date, format) - datetime.datetime.strptime(
        start_date, format
    )
    return result.days


def get_daily_start_end_date(format: str) -> tuple:
    end_date = datetime.date.today().strftime(format)
    start_date = (datetime.date.today() + datetime.timedelta(days=-1)).strftime(format)
    return (start_date, end_date)


def add_day_from_timestamp(
    timestamp: float, days: int, format: str = None, offset: float = 0
) -> str:
    return (
        datetime.datetime.fromtimestamp(
            timestamp, datetime.timezone(datetime.timedelta(hours=offset))
        )
        + datetime.timedelta(days=days)
    ).strftime(format)
