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

with open('../NFTLoan/NFTLoan/bin/sc/NFTFlashLoan.nef', 'rb') as f:
    nef_file = f.read()
with open('../NFTLoan/NFTLoan/bin/sc/NFTFlashLoan.manifest.json', 'r') as f:
    manifest_dict = json.loads(f.read())
    manifest_dict['name'] = 'AnyUpdateShortSafe'
    manifest = json.dumps(manifest_dict, separators=(',', ':'))

FAULT_MESSAGE = 'ASSERT is executed with false result.'

client = TestClient(target_url, anyupdate_short_safe_hash, wallet_address, wallet_path, wallet_password, signer=signer,
                    with_print=True)
# client.openwallet()

session = 'NophtD'
print(client.new_snapshots_from_current_system(session))
print(client.list_snapshots())
client.invokefunction('putStorage', params=[0x02, 1], session=session)


def query_all_registered_rental(external_token_id=1, internal_token_id=1):
    with_print = client.with_print
    client.with_print = False
    print(client.invokefunction('anyUpdate',
                                params=[nef_file, manifest, 'listRegisteredRentalByToken', [test_nopht_d_hash]],
                                session=session))
    print(client.invokefunction('anyUpdate',
                                params=[nef_file, manifest, 'listRegisteredRentalByToken',
                                        [test_nopht_d_hash, external_token_id]],
                                session=session))
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'getRegisteredRentalByToken',
                                                     [test_nopht_d_hash, external_token_id, wallet_scripthash]],
                                session=session))
    print(client.invokefunction('anyUpdate',
                                params=[nef_file, manifest, 'listRegisteredRentalByToken', [anyupdate_short_safe_hash]],
                                session=session))
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listRegisteredRentalByToken',
                                                     [anyupdate_short_safe_hash, internal_token_id]], session=session))
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'getRegisteredRentalByToken',
                                                     [anyupdate_short_safe_hash, internal_token_id, wallet_scripthash]],
                                session=session))
    print(client.invokefunction('anyUpdate',
                                params=[nef_file, manifest, 'listRegisteredRentalByRenter', [wallet_scripthash]],
                                session=session))
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listRegisteredRentalByRenter',
                                                     [wallet_scripthash, test_nopht_d_hash]], session=session))
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listRegisteredRentalByRenter',
                                                     [wallet_scripthash, anyupdate_short_safe_hash]], session=session))
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'getRegisteredRentalByRenter',
                                                     [wallet_scripthash, test_nopht_d_hash, external_token_id]],
                                session=session))
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'getRegisteredRentalByRenter',
                                                     [wallet_scripthash, anyupdate_short_safe_hash, internal_token_id]],
                                session=session))
    client.with_print = with_print


print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'registerRental',
                                                 [wallet_scripthash, test_nopht_d_hash, 68, 1, 5, 7, True]],
                            session=session))
query_all_registered_rental()
print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'registerRental',
                                                 [wallet_scripthash, test_nopht_d_hash, 32, 1, 5, 7, True]],
                            session=session))
assert client.invokefunction('anyUpdate', params=[nef_file, manifest, 'registerRental',
                                                  [wallet_scripthash, test_nopht_d_hash, 1, 1, 5, 7, True]],
                             do_not_raise_on_result=True, session=session) == FAULT_MESSAGE
query_all_registered_rental()

client.set_snapshot_timestamp(session, int((time.time() + 500) * 1000))
