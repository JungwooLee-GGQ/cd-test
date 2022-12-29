import os
import logging
import sys

sys.path.append(os.getcwd())
import requests
import datetime
from utils.patch import Patch
from app.core.log_config import log_config
from app.collector.match_collector import MatchCollector, TierGroup

DOWNLOAD_SERVER = "http://121.78.136.227:8002/ai/download/v1/match/list"
SAVE_FILE_FOLDER = "save_files"
MIN_PATCH_PER_MATCH = 400
MATCH_PER_DAY = 12  # collected match per tier (ex. 30 and average days for patches are 14 then can gain 420 games per patch)
USER_COUNT = 3200  # user sampling count

log_config()
logger = logging.getLogger(__name__)

tier_list = [
    # TierGroup.B12,
    TierGroup.B34,
    # TierGroup.S12,
    # TierGroup.S34,
    # TierGroup.G12,
    # TierGroup.G34,
    # TierGroup.P12,
    # TierGroup.P34,
    # TierGroup.D12,
    # TierGroup.D34,
    # TierGroup.M1,
]
# collect tier match
for tier_group in tier_list:
    collector = MatchCollector(tier_group=tier_group)
    collector.collect_tier_match(
        count_to_collect=MATCH_PER_DAY,
        user_count=USER_COUNT,
        start_date="2022-12-7",
        end_date="2022-12-29",
    )
    logger.info(f"Tier: {tier_group} complete collecting")
# collect Apex match
collector = MatchCollector(TierGroup.A)
collector.collect_all_match(start_date="2022-12-28", end_date="2022-12-29")
logger.info(f"Tier: {TierGroup.A} complete collecting")

current_version = Patch.get_current_version()
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
            count = len(f.readlines())
            if count < MIN_PATCH_PER_MATCH:
                logger.warning(
                    f"Tier {tier_group} is lacking {MIN_PATCH_PER_MATCH - count} files"
                )
