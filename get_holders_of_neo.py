from typing import Dict, List, Tuple, Union
import base64
from neo_fairy_client import FairyClient, NeoAddress, GasAddress, Hash160Str, PublicKeyStr

client = FairyClient()

neo_storage: Dict[str, str] = client.find_storage_with_session(b'\x14', contract_scripthash=NeoAddress)
neo_storage: List[Tuple[Hash160Str, str]] = [
    (FairyClient.bytes_to_Hash160Str(base64.b64decode(k)[1:]), v)
    for k, v in neo_storage.items()
]
data = [(balance, since_block, PublicKeyStr(vote_to.hex()) if vote_to else None) for balance, since_block, vote_to, last_GAS_per_vote in client.deserialize([v for _, v in neo_storage])]
neo_storage: List[Tuple[Hash160Str, int, int, Union[None, PublicKeyStr]]] = [
    (k, balance, since_block, vote_to) for (k, v), (balance, since_block, vote_to) in zip(neo_storage, data)
]
for k, balance, since_block, vote_to in neo_storage:
    assert type(k) is Hash160Str
    assert type(balance) is int
    assert type(since_block) is int
    assert vote_to is None or type(vote_to) is PublicKeyStr
print('NEO holders count:', len(neo_storage))
print('Sum of NEO balance', sum([data[1] for data in neo_storage]))
voted_neo = [(k, balance, since_block, vote_to) for (k, balance, since_block, vote_to) in neo_storage if vote_to]
print('NEO voters count:', len(voted_neo))
print('NEO voted balance:', sum([balance for (k, balance, since_block, vote_to) in voted_neo]))
neo_storage.sort(key=lambda data: data[1], reverse=True)
sum_ = 100000000
for data in neo_storage:
    sum_ -= data[1]
    print(f'{data[0].to_address()}: {data[1]}; {sum_}')
