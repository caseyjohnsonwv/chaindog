import re
from thefuzz import fuzz
from typing import List, Tuple


class NLPException(Exception):
    pass


# temporary bad solution - can we do semantic matching?
class ActionKeywords:
    DELETE = ['delete', 'cancel', 'end', 'forget', 'stop']
    UPDATE = ['change', 'edit', 'extend', 'modify', 'update']


def extract_park_name(msg:str, park_names:List[str]) -> str:
    res = _extract_best_match(msg, park_names, threshold=30)
    if res is None:
        raise NLPException
    index, _ = res
    return park_names[index]


def extract_ride_name(msg:str, ride_names:List[str]) -> str:
    res = _extract_best_match(msg, ride_names, threshold=50)
    if res is None:
        raise NLPException
    index, _ = res
    return ride_names[index]


def extract_wait_time(msg:str) -> int:
    # crude regex matching for now
    matches = re.findall('\d+', msg)
    if len(matches) > 0:
        wait_time = matches[0]
        return int(wait_time)


def detect_deletion_message(msg:str) -> bool:
    # temporary bad solution - can we do semantic matching?
    _, word = _extract_best_match(msg, ActionKeywords.DELETE, threshold=90)
    return False if word is None else True


# def detect_update_message(msg:str) -> bool:
#     # temporary bad solution - can we do semantic matching?
#     _, word = _extract_best_match(msg, ActionKeywords.UPDATE, threshold=90)
#     return False if word is None else True


### HELPER FUNCTIONS ###


def _extract_best_match(msg:str, match_list:List[str], threshold:int=0) -> Tuple[int, str]:
    closest_match_index, best_ratio = None, 0
    for i,attempt in enumerate(match_list):
        ratio = fuzz.token_set_ratio(msg, attempt)
        if ratio > best_ratio:
            closest_match_index = i
            best_ratio = ratio
        if ratio == 100:
            break
    if best_ratio > threshold:
        return closest_match_index, match_list[closest_match_index]
    else:
        return -1, None
