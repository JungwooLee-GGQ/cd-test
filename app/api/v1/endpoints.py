from __future__ import annotations
import threading
from fastapi import APIRouter, HTTPException
from app.collector.match_collector import MatchCollector, TierGroup
from utils import patch

router = APIRouter()
collecting_threads: list[threading.Thread] = []


@router.get("/status/{version}")
async def show_status(version: str):
    version = version or patch.get_current_version()
    return MatchCollector.get_sampling_status(version)


@router.get("/groups/{tier_groups}")
async def start_group_collecting(tier_groups: str, count=400):
    groups = []
    for tier_group in tier_groups.split(","):
        groups.append(validate_and_convert_tier_group(tier_group))
    count = validate_count(count)
    t = threading.Thread(target=run_group_collecting, args=(groups, count))
    t.start()
    collecting_threads.append(t)
    collecting_threads[:] = [th for th in collecting_threads if th.is_alive()]
    return {"collecting threads": len(collecting_threads)}


@router.get("/group/{tier_group}")
async def start_collecting(tier_group: str, count=400):
    group = validate_and_convert_tier_group(tier_group)
    count = validate_count(count)
    t = threading.Thread(target=run_collecting, args=(group, count))
    t.start()
    collecting_threads.append(t)
    collecting_threads[:] = [th for th in collecting_threads if th.is_alive()]
    return {"collecting threads": len(collecting_threads)}


def validate_and_convert_tier_group(tier_group: str) -> TierGroup:
    try:
        return TierGroup[tier_group]
    except KeyError:
        raise HTTPException(
            status_code=404, detail=f"There is no tier group '{tier_group}'."
        )


def validate_count(count) -> int:
    try:
        return int(count)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"count '{count}' is not number.")


def run_collecting(group: TierGroup, count: int):
    MatchCollector(group).match_sampling(count)


def run_group_collecting(groups: list[TierGroup], count: int):
    for group in groups:
        run_collecting(group, count)
