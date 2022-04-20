import json
import time
from neo_test_client.rpc import TestClient
from neo_test_client.utils.types import Hash160Str, Signer, WitnessScope

target_url = 'http://127.0.0.1:10332'
wallet_address = 'Nb2CHYY5wTh2ac58mTue5S3wpG6bQv5hSY'
wallet_scripthash = Hash160Str.from_address(wallet_address)
wallet_path = 'testnet.json'
wallet_password = '1'

signer = Signer(wallet_scripthash, scopes=WitnessScope.Global)

anyupdate_short_safe_hash = Hash160Str('0x5c1068339fae89eb1a743909d0213e1d99dc5dc9')  # AnyUpdate short safe
test_nopht_d_hash = Hash160Str('0x2a6cd301cad359fc85e42454217e51485fffe745')

with open('getTimeContract.nef', 'rb') as f:
    nef_file = f.read()
with open('getTimeContract.manifest.json', 'r') as f:
    manifest_dict = json.loads(f.read())
    manifest_dict['name'] = 'AnyUpdateShortSafe'
    manifest = json.dumps(manifest_dict, separators=(',', ':'))

client = TestClient(target_url, anyupdate_short_safe_hash, wallet_address, wallet_path, wallet_password, signer=signer,
                    with_print=True)
# client.openwallet()

session = 'Runtime.Time'
print(client.new_snapshots_from_current_system(session))
print(client.list_snapshots())
timestamp_dict = client.get_snapshot_timestamp(session)
timestamp_returned_from_contract = client.invokefunction('anyUpdate', params=[nef_file, manifest, 'getTime', []], session=session)
print(timestamp_dict, timestamp_returned_from_contract)
assert timestamp_dict[session] == 0
print(client.set_snapshot_timestamp(session, int(time.time() + 86400) * 1000))
print(timestamp_returned_from_contract := client.invokefunction('anyUpdate', params=[nef_file, manifest, 'getTime', []], session=session))
print(timestamp_dict := client.get_snapshot_timestamp(session))
assert timestamp_dict[session] == timestamp_returned_from_contract
