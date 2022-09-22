from typing import Any, List


def to_list(element: Any) -> List:
    if element is list:
        return element
    if element is not None:
        return [element]
    return []
