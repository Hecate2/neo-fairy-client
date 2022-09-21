import json
import time
from neo_fairy_client.rpc import FairyClient
from neo_fairy_client.utils.types import Hash160Str, Signer, WitnessScope

target_url = 'http://127.0.0.1:16868'
wallet_address = 'Nb2CHYY5wTh2ac58mTue5S3wpG6bQv5hSY'
wallet_scripthash = Hash160Str.from_address(wallet_address)
wallet_path = 'testnet.json'
wallet_password = '1'

signer = Signer(wallet_scripthash, scopes=WitnessScope.Global)

with open('../AnyUpdate/AnyUpdateShortSafe.nef', 'rb') as f:
    anyupdate_nef_file = f.read()
with open('../AnyUpdate/AnyUpdateShortSafe.manifest.json', 'r') as f:
    anyupdate_manifest = f.read()

with open('../NFTLoan/NophtD/bin/sc/TestNophtD.nef', 'rb') as f:
    test_nopht_d_nef = f.read()
with open('../NFTLoan/NophtD/bin/sc/TestNophtD.manifest.json', 'r') as f:
    test_nopht_d_manifest = f.read()

with open('getTimeContract.nef', 'rb') as f:
    nef_file = f.read()
with open('getTimeContract.manifest.json', 'r') as f:
    manifest_dict = json.loads(f.read())
    manifest_dict['name'] = 'AnyUpdateShortSafe'
    manifest = json.dumps(manifest_dict, separators=(',', ':'))

session = 'Runtime.Time'
client = FairyClient(target_url, wallet_address, wallet_path, wallet_password, signers=signer,
                     with_print=True, fairy_session=session)
print(client.new_snapshots_from_current_system())
print(client.list_snapshots())

client.open_fairy_wallet()
client.set_gas_balance(100_0000_0000)
anyupdate_short_safe_hash = client.virtual_deploy(anyupdate_nef_file, anyupdate_manifest)
test_nopht_d_hash = client.virtual_deploy(test_nopht_d_nef, test_nopht_d_manifest)
client.contract_scripthash = anyupdate_short_safe_hash

timestamp_dict = client.get_snapshot_timestamp()
timestamp_returned_from_contract = client.invokefunction('anyUpdate', params=[nef_file, manifest, 'getTime', []], rpc_server_session=session)
print(timestamp_dict, timestamp_returned_from_contract)
assert timestamp_dict[session] is None
print(client.set_snapshot_timestamp(timestamp := int(time.time() + 86400) * 1000, session))
print(timestamp_returned_from_contract := client.invokefunction('anyUpdate', params=[nef_file, manifest, 'getTime', []], rpc_server_session=session))
print(timestamp_dict := client.get_snapshot_timestamp())
assert timestamp_dict[session] == timestamp_returned_from_contract == timestamp
print(client.set_snapshot_timestamp(None))
assert client.get_snapshot_timestamp()[session] is None
second_timestamp_returned_from_contract = client.invokefunction('anyUpdate', params=[nef_file, manifest, 'getTime', []], rpc_server_session=session)
assert abs(timestamp_returned_from_contract - second_timestamp_returned_from_contract - 86400_000) < 45_000  # may fail if a block really lags behind
