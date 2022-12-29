import multiprocessing
from multiprocessing.pool import ThreadPool
from tqdm import tqdm


def write_text(path: str, content: str, command: str):
    with open(path, command, encoding="utf-8") as f_out:
        f_out.write(content)
        f_out.flush()


def rank_to_number(tier: str, division: str) -> int:
    if division == "" and tier == "":
        return 0
    if division == "I":
        index = 0
    elif division == "II":
        index = -1
    elif division == "III":
        index = -2
    elif division == "IV":
        index = -3
    else:
        raise ValueError(f"Division is not valid: {division}")

    if tier == "IRON":
        index += 4 * 1
    elif tier == "BRONZE":
        index += 4 * 2
    elif tier == "SILVER":
        index += 4 * 3
    elif tier == "GOLD":
        index += 4 * 4
    elif tier == "PLATINUM":
        index += 4 * 5
    elif tier == "DIAMOND":
        index += 4 * 6
    elif tier == "MASTER":
        index += 4 * 6 + 1
    elif tier == "GRANDMASTER":
        index += 4 * 6 + 2
    elif tier == "CHALLENGER":
        index += 4 * 6 + 3
    else:
        raise ValueError(f"Tier is not valid: {tier}")
    return index


def run_multithread(func, iter, update=lambda x: None, use_tqdm=False, tqdm_decs=""):
    """Apply a function to an iterable and update the results with
    an update function through multi-thread
    """
    cpu_count = multiprocessing.cpu_count()
    MAX_THREAD = 8

    with ThreadPool(min(cpu_count, MAX_THREAD)) as pool:
        if use_tqdm:
            item_count = len(iter)
            for result in tqdm(
                pool.imap_unordered(func, iter),
                total=item_count,
                desc=tqdm_decs,
            ):
                update(result)

        else:
            for result in pool.imap_unordered(func, iter):
                update(result)
