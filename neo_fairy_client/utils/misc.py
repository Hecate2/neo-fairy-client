from typing import Any


def to_list(element: Any):
    if element is list:
        return element
    if element is not None:
        return [element]
    return element
