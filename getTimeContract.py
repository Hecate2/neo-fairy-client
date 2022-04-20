from boa3.builtin import public
from boa3.builtin.interop.runtime import time


@public
def getTime() -> int:
    return time
