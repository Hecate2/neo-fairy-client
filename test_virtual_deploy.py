import json
from neo_test_client.rpc import TestClient
from neo_test_client.utils.types import Hash160Str, Signer, WitnessScope
from neo_test_client.utils.timers import gen_timestamp_and_date_str_in_seconds

target_url = 'http://127.0.0.1:10332'  # to testnet, not mainnet
wallet_address = 'Nb2CHYY5wTh2ac58mTue5S3wpG6bQv5hSY'
wallet_scripthash = Hash160Str.from_address(wallet_address)
wallet_path = 'testnet.json'
wallet_password = '1'

borrower_address = 'NaainHz563mJLsHRsPD4NrKjMEQGBXXJY9'
borrower_scripthash = Hash160Str.from_address(borrower_address)
borrower_wallet_path = 'user1.json'

lender = Signer(wallet_scripthash, scopes=WitnessScope.Global)
borrower = Signer(borrower_scripthash, scopes=WitnessScope.Global)

anyupdate_short_safe_hash = Hash160Str('0x5c1068339fae89eb1a743909d0213e1d99dc5dc9')  # AnyUpdate short safe
test_nopht_d_hash = Hash160Str('0x2a6cd301cad359fc85e42454217e51485fffe745')

with open('../NFTLoan/NFTLoan/bin/sc/NFTFlashLoan.nef', 'rb') as f:
    nef_file = f.read()
with open('../NFTLoan/NFTLoan/bin/sc/NFTFlashLoan.manifest.json', 'r') as f:
    manifest = f.read()

FAULT_MESSAGE = 'ASSERT is executed with false result.'

rpc_server_session = 'NophtD'
lender_client = TestClient(target_url, anyupdate_short_safe_hash, wallet_address, wallet_path, wallet_password, rpc_server_session=rpc_server_session, signer=lender, with_print=True)
borrower_client = TestClient(target_url, anyupdate_short_safe_hash, borrower_address, borrower_wallet_path, wallet_password, rpc_server_session=rpc_server_session, signer=borrower, with_print=True)
print(lender_client.delete_snapshots(lender_client.list_snapshots()))
lender_client.openwallet()
scripthash = lender_client.virtual_deploy(rpc_server_session, nef_file, manifest)
print(scripthash)
assert scripthash == lender_client.virtual_deploy(rpc_server_session, nef_file, manifest)
lender_client.closewallet()
lender_client.contract_scripthash = scripthash
print(lender_client.invokefunction('registerRental', [wallet_scripthash, test_nopht_d_hash, 68, 1, 5, 7, True]))
