from typing import Dict, List, Tuple
import base64
from neo_fairy_client import FairyClient, GasAddress, UInt160, Hash160Str

client = FairyClient()

gas_storage: Dict[str, str] = client.find_storage_with_session('', None, GasAddress)
gas_storage: List[Tuple[Hash160Str, str]] = [
    (FairyClient.bytes_to_Hash160Str(base64.b64decode(k)[1:]), v)
    for k, v in gas_storage.items()
    if base64.b64decode(k).startswith(b'\x14')
]
balances = [i[0] for i in client.deserialize([v for _, v in gas_storage])]
gas_storage: List[Tuple[Hash160Str, int]] = [
    (k, b) for (k, v), b in zip(gas_storage, balances)
]
# for k, v in gas_storage:
#     print(k, v)
for k, v in gas_storage:
    assert type(k) is Hash160Str
    assert type(v) is int
print(len(gas_storage))