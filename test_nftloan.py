import json
import time
from neo_test_client.rpc import TestClient
from neo_test_client.utils.types import Hash160Str, Signer, WitnessScope
from neo_test_client.utils.timers import gen_timestamp_and_date_str_in_seconds

target_url = 'http://127.0.0.1:10332'
wallet_address = 'Nb2CHYY5wTh2ac58mTue5S3wpG6bQv5hSY'
wallet_scripthash = Hash160Str.from_address(wallet_address)
wallet_path = 'testnet.json'
wallet_password = '1'

borrower_address = 'NaainHz563mJLsHRsPD4NrKjMEQGBXXJY9'
borrower_scripthash = Hash160Str.from_address(borrower_address)

lender = Signer(wallet_scripthash, scopes=WitnessScope.Global)
borrower = Signer(borrower_scripthash, scopes=WitnessScope.Global)

anyupdate_short_safe_hash = Hash160Str('0x5c1068339fae89eb1a743909d0213e1d99dc5dc9')  # AnyUpdate short safe
test_nopht_d_hash = Hash160Str('0x2a6cd301cad359fc85e42454217e51485fffe745')

with open('../NFTLoan/NFTLoan/bin/sc/NFTFlashLoan.nef', 'rb') as f:
    nef_file = f.read()
with open('../NFTLoan/NFTLoan/bin/sc/NFTFlashLoan.manifest.json', 'r') as f:
    manifest_dict = json.loads(f.read())
    manifest_dict['name'] = 'AnyUpdateShortSafe'
    manifest = json.dumps(manifest_dict, separators=(',', ':'))

FAULT_MESSAGE = 'ASSERT is executed with false result.'

rpc_server_session = 'NophtD'
lender_client = TestClient(target_url, anyupdate_short_safe_hash, wallet_address, wallet_path, wallet_password, rpc_server_session=rpc_server_session, signer=lender, with_print=True)
borrower_client = TestClient(target_url, anyupdate_short_safe_hash, wallet_address, wallet_path, wallet_password, rpc_server_session=rpc_server_session, signer=borrower, with_print=True)
# client.openwallet()

print(lender_client.new_snapshots_from_current_system())
print(lender_client.list_snapshots())
lender_client.invokefunction('putStorage', params=[0x02, 1])


def query_all_registered_rental(client=lender_client, external_token_id=1, internal_token_id=1):
    with_print, function_default_relay = client.with_print, client.function_default_relay
    client.with_print, client.function_default_relay = False, False
    print('====listRegisteredRentalByToken')
    print('external token')
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listRegisteredRentalByToken', [test_nopht_d_hash]]))
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listRegisteredRentalByToken', [test_nopht_d_hash, external_token_id]]))
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'getRegisteredRentalByToken', [test_nopht_d_hash, external_token_id, wallet_scripthash]]))
    print('internal token')
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listRegisteredRentalByToken', [anyupdate_short_safe_hash]]))
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listRegisteredRentalByToken', [anyupdate_short_safe_hash, internal_token_id]]))
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'getRegisteredRentalByToken', [anyupdate_short_safe_hash, internal_token_id, wallet_scripthash]]))
    print('====listRegisteredRentalByRenter')
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listRegisteredRentalByRenter', [wallet_scripthash]]))
    print('external token')
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listRegisteredRentalByRenter', [wallet_scripthash, test_nopht_d_hash]]))
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'getRegisteredRentalByRenter', [wallet_scripthash, test_nopht_d_hash, external_token_id]]))
    print('internal token')
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listRegisteredRentalByRenter', [wallet_scripthash, anyupdate_short_safe_hash]]))
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'getRegisteredRentalByRenter', [wallet_scripthash, anyupdate_short_safe_hash, internal_token_id]]))
    print('====listRentalDeadlineByRenter')
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listRentalDeadlineByRenter', [wallet_scripthash]]))
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listRentalDeadlineByRenter', [wallet_scripthash, test_nopht_d_hash]]))
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listRentalDeadlineByRenter', [wallet_scripthash, test_nopht_d_hash, external_token_id]]))
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listRentalDeadlineByRenter', [wallet_scripthash, test_nopht_d_hash, external_token_id, borrower_scripthash]]))
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listRentalDeadlineByRenter', [wallet_scripthash, anyupdate_short_safe_hash]]))
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listRentalDeadlineByRenter', [wallet_scripthash, anyupdate_short_safe_hash, internal_token_id]]))
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listRentalDeadlineByRenter', [wallet_scripthash, anyupdate_short_safe_hash, internal_token_id, borrower_scripthash]]))
    print('====listRentalDeadlineByTenant')
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listRentalDeadlineByTenant', [borrower_scripthash]]))
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listRentalDeadlineByTenant', [borrower_scripthash, test_nopht_d_hash]]))
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listRentalDeadlineByTenant', [borrower_scripthash, test_nopht_d_hash, external_token_id]]))
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listRentalDeadlineByTenant', [borrower_scripthash, test_nopht_d_hash, external_token_id, wallet_scripthash]]))
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listRentalDeadlineByTenant', [borrower_scripthash, anyupdate_short_safe_hash]]))
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listRentalDeadlineByTenant', [borrower_scripthash, anyupdate_short_safe_hash, internal_token_id]]))
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listRentalDeadlineByTenant', [borrower_scripthash, anyupdate_short_safe_hash, internal_token_id, wallet_scripthash]]))
    client.with_print, client.function_default_relay = with_print, function_default_relay


print(lender_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'registerRental', [wallet_scripthash, test_nopht_d_hash, 68, 1, 5, 7, True]]))
query_all_registered_rental()
print(lender_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'registerRental', [wallet_scripthash, test_nopht_d_hash, 32, 1, 10, 7, True]]))
print(lender_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'setRentalPrice', [wallet_scripthash, test_nopht_d_hash, 1, 10]]))
print(lender_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'setRentalPrice', [wallet_scripthash, anyupdate_short_safe_hash, 1, 3]]))
assert lender_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'registerRental', [wallet_scripthash, test_nopht_d_hash, 1, 1, 5, 7, True]], do_not_raise_on_result=True) == FAULT_MESSAGE
query_all_registered_rental()
print(lender_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listExternalTokenInfo', [0]]))
print(lender_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listExternalTokenInfo', [1]]))
print(lender_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'getExternalTokenInfo', [1]]))
print(lender_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listInternalTokenId', [test_nopht_d_hash]]))
print(lender_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listInternalTokenId', [test_nopht_d_hash, 0]]))
print(lender_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listInternalTokenId', [test_nopht_d_hash, 1]]))
print(lender_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'getInternalTokenId', [test_nopht_d_hash, 1]]))

borrow_timestamp, _ = gen_timestamp_and_date_str_in_seconds(0)
lender_client.set_snapshot_timestamp(rpc_server_session, borrow_timestamp)

print(borrower_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'borrow', [wallet_scripthash, borrower_scripthash, 10, 1, 16000]]))
