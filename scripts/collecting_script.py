import datetime
import logging
import os
import sys

import requests

sys.path.append(os.getcwd())

from app import APIAccess
from app.collector.match_collector import MatchCollector, TierGroup
from app.core.log_config import log_config
from utils.patch import Patch

DOWNLOAD_SERVER = "http://121.78.136.227:8002/ai/download/v1/match/list"
SAVE_FILE_FOLDER = "save_files"
MIN_PATCH_PER_MATCH = 400
MATCH_PER_DAY = 30  # collected match per tier (ex. 30 and average days for patches are 14 then can gain 420 games per patch)
USER_COUNT = 3200  # user sampling count

log_config()
logger = logging.getLogger(__name__)

tier_list = [
    TierGroup.B12,
    TierGroup.B34,
    TierGroup.S12,
    TierGroup.S34,
    TierGroup.G12,
    TierGroup.G34,
    TierGroup.P12,
    TierGroup.P34,
    TierGroup.D12,
    TierGroup.D34,
    TierGroup.M1,
]
# collect tier match
for tier_group in tier_list:
    collector = MatchCollector(tier_group=tier_group)
    collector.collect_tier_match(
        count_to_collect=MATCH_PER_DAY,
        user_count=USER_COUNT,
        is_daily_collect=True,
        renew_sampling=False,
    )
    logger.info(f"Tier: {tier_group} complete collecting")
# collect Apex match
collector = MatchCollector(TierGroup.A)
collector.collect_all_match(is_daily_collect=True, renew_sampling=False)
logger.info(f"Tier: {TierGroup.A} complete collecting")

current_version = Patch.get_current_version()
tier_list = []
# request to download server
tier_list.append(TierGroup.A)
for tier_group in tier_list:
    logger.info(f"Tier: {tier_group} - Starting to post request to download server")
    file_dir = os.path.join(
        os.getcwd(),
        SAVE_FILE_FOLDER,
        current_version,
        f"{tier_group.name}_match_list.txt",
    )
    with open(file=file_dir, mode="rb") as file:
        upload = {"match_list_file": file}
        obj = {"version": current_version, "local_save": False}
        res = requests.post(DOWNLOAD_SERVER, files=upload, data=obj)
        if res.status_code == 200:
            logger.info(
                f"Tier: {tier_group} - Complete to post request to download server"
            )
            queue = res.json()["current_queue"]
            logger.info(f"current download queue: {queue}")
        else:
            logger.warning(res.text)

# log for day before patch
current_version = Patch.get_current_version()
today = datetime.datetime.today()
format = "%Y-%m-%d"
timezone_offset = 9

next_patch_timestamp = Patch.get_next_patch_start_timestamp(current_version)
day_before_next_patch = datetime.datetime.fromtimestamp(
    next_patch_timestamp, datetime.timezone(datetime.timedelta(hours=timezone_offset))
) + datetime.timedelta(days=-1)
if (
    today.strftime(format) == day_before_next_patch.strftime(format)
    and next_patch_timestamp != -1
):
    for tier_group in tier_list:
        file_dir = os.path.join(
            os.getcwd(),
            SAVE_FILE_FOLDER,
            current_version,
            f"{tier_group.name}_match_list.txt",
        )
        with open(file=file_dir, mode="r") as f:
            matches = f.readlines()
            count = len(matches)
            latest_matche = matches[-1].replace("\n", "")
            end_time = APIAccess.get_match_data(match_id=latest_matche).end_time
            latest_date = datetime.datetime.fromtimestamp(end_time / 1000)
            if count < MIN_PATCH_PER_MATCH:
                logger.warning(
                    f"Tier: {tier_group} is lacking {MIN_PATCH_PER_MATCH - count} matches"
                )
            else:
                logger.info(f"Tier: {tier_group} currently has {count} matches")
