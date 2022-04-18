from typing import Union
import time


def sleep_until(timestamp_millisecond: Union[int, float], accuracy = 0.5):
    print(f'sleep until timestamp (millisecond): {timestamp_millisecond}')
    timestamp = timestamp_millisecond / 1000
    while time.time() < timestamp:
        time.sleep(accuracy)


def sleep_for_next_block(sleep_seconds=15):
    print(f'sleep {sleep_seconds} seconds waiting for the next block')
    time.sleep(sleep_seconds)
