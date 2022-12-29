import datetime


def utc_time_to_timestamp(time_string: str, format: str = None) -> float:
    """Convert time string in UTC(GMT, or Zulu time) to Unix timestamp

    The default time format follows ISO 8601 (%Y-%m-%dT%H:%M:%S.%fZ or %Y-%m-%dT%H:%M:%SZ)

    time_string: time string in UTC+0
    format: the format by which time string is written
    """
    if not format:
        if "." in time_string:
            format = "%Y-%m-%dT%H:%M:%S.%fZ"
        else:
            format = "%Y-%m-%dT%H:%M:%SZ"
    return (
        datetime.datetime.strptime(time_string, format)
        .replace(tzinfo=datetime.timezone.utc)
        .timestamp()
    )
