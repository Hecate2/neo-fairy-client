import json
from neo_fairy_client.rpc import FairyClient
from neo_fairy_client.utils.types import Hash160Str

target_url = 'http://127.0.0.1:16868'
wallet_address = 'Nb2CHYY5wTh2ac58mTue5S3wpG6bQv5hSY'
wallet_scripthash = Hash160Str.from_address(wallet_address)

with open('getRandomContract.nef', 'rb') as f:
    nef_file = f.read()
with open('getRandomContract.manifest.json', 'r') as f:
    manifest_dict = json.loads(f.read())
    manifest_dict['name'] = 'AnyUpdateShortSafe'
    manifest = json.dumps(manifest_dict, separators=(',', ':'))

fairy_session = 'random'
client = FairyClient(target_url, wallet_address, fairy_session=fairy_session, with_print=False)
client.new_snapshots_from_current_system()
client.set_gas_balance(100_0000_0000)
client.contract_scripthash = client.virtual_deploy(nef_file, manifest)
print(first_result := client.invokefunction('getRandom'))
print(client.set_snapshot_random(0))
assert client.get_snapshot_random()[fairy_session] == 0
assert client.invokefunction('getRandom') == 0
print(client.set_snapshot_random(None))
assert client.get_snapshot_random()[fairy_session] is None
assert client.invokefunction('getRandom') == first_result
