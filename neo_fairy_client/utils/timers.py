from typing import Union, Tuple
import datetime
from math import ceil
import time


def gen_timestamp_and_date_str_in_days(days: int) -> Tuple[int, str]:
    today = datetime.date.today()
    days_later = today + datetime.timedelta(days=days)
    days_later_ending_milisecond = (int(time.mktime(time.strptime(str(days_later), '%Y-%m-%d')) + 86400) * 1000 - 1)
    days_later_date_str = days_later.strftime('%m_%d_%Y')
    return days_later_ending_milisecond, days_later_date_str


def gen_timestamp_and_date_str_in_seconds(seconds: int) -> Tuple[int, str]:
    current_time = time.time()
    today = datetime.date.fromtimestamp(current_time)
    seconds_later = today + datetime.timedelta(seconds=seconds)
    seconds_later_date_str = seconds_later.strftime('%m_%d_%Y') + str(ceil(current_time)+seconds)
    return ceil((current_time + seconds) * 1000), seconds_later_date_str


def sleep_until(timestamp_millisecond: Union[int, float], accuracy = 0.5):
    print(f'sleep until timestamp (millisecond): {timestamp_millisecond}')
    timestamp = timestamp_millisecond / 1000
    while time.time() < timestamp:
        time.sleep(accuracy)


def sleep_for_next_block(sleep_seconds=15):
    print(f'sleep {sleep_seconds} seconds waiting for the next block')
    time.sleep(sleep_seconds)
