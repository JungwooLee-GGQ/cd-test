import os
from api_client.value_object import TierGroup


TARGET_DIR = (
    r"C:\Users\User\PythonProject\ai-python-coach-gathering-server\save_files\12.22"
)
MATCH_TIER = TierGroup.A.name
SPLIT = 5

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

file_dir = os.path.join(TARGET_DIR, f"{MATCH_TIER}_match_list.txt")
with open(file=file_dir, mode="r") as f:
    matches = f.readlines()
    count = len(matches)
    start = 0
    for i in range(SPLIT):
        if i != SPLIT - 1:
            print(start, count // SPLIT)
            splited = matches[start : start + count // SPLIT]
            start = start + count // SPLIT
        else:
            splited = matches[start:]
        file_name = os.path.join(TARGET_DIR, f"splited_{MATCH_TIER}_match_{i+1}.txt")
        with open(file=file_name, mode="w") as sub_f:
            sub_f.writelines(splited)
