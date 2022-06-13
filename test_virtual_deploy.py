import base64
from neo_test_client.rpc import TestClient
from neo_test_client.utils.types import Hash160Str, Signer, WitnessScope
from neo_test_client.utils.interpreters import Interpreter

target_url = 'http://127.0.0.1:16868'
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

with open('../NFTLoan/NophtD/bin/sc/TestNophtD.nef', 'rb') as f:
    nophtd_nef_file = f.read()
with open('../NFTLoan/NophtD/bin/sc/TestNophtD.manifest.json', 'r') as f:
    nophtd_manifest = f.read()
with open('../NFTLoan/NFTLoan/bin/sc/NFTFlashLoan.nef', 'rb') as f:
    nef_file = f.read()
with open('../NFTLoan/NFTLoan/bin/sc/NFTFlashLoan.manifest.json', 'r') as f:
    manifest = f.read()

FAULT_MESSAGE = 'ASSERT is executed with false result.'

rpc_server_session = 'NophtD'
lender_client = TestClient(target_url, anyupdate_short_safe_hash, wallet_address, wallet_path, wallet_password, rpc_server_session=rpc_server_session, signer=lender, with_print=True)
borrower_client = TestClient(target_url, anyupdate_short_safe_hash, borrower_address, borrower_wallet_path, wallet_password, rpc_server_session=rpc_server_session, signer=borrower, with_print=True)
print(lender_client.delete_snapshots(lender_client.list_snapshots()))
lender_client.open_fairy_wallet()
lender_client.new_snapshots_from_current_system(rpc_server_session)
lender_client.set_gas_balance(100_0000_0000)
test_nopht_d_hash = lender_client.virtual_deploy(nophtd_nef_file, nophtd_manifest)
nftloan_scripthash = lender_client.virtual_deploy(nef_file, manifest)
print(test_nopht_d_hash, nftloan_scripthash)
assert nftloan_scripthash == lender_client.virtual_deploy(nef_file, manifest)
lender_client.contract_scripthash = test_nopht_d_hash
lender_client.close_fairy_wallet()
print(lender_client.invokefunction('totalSupply'))
print(lender_client.invokefunction('balanceOf', params=[wallet_scripthash]))
print(lender_client.invokefunction('balanceOf', params=[wallet_scripthash, 1]))
lender_client.contract_scripthash = nftloan_scripthash
assert lender_client.get_storage_with_session(2) == {base64.b64encode(Interpreter.int_to_bytes(2)).decode():base64.b64encode(Interpreter.int_to_bytes(1)).decode()}
lender_client.put_storage_with_session(2, 0)
assert lender_client.get_storage_with_session(2) == {base64.b64encode(Interpreter.int_to_bytes(2)).decode():None}
lender_client.put_storage_with_session(2, 1)
assert lender_client.get_storage_with_session(2) == {base64.b64encode(Interpreter.int_to_bytes(2)).decode():base64.b64encode(Interpreter.int_to_bytes(1)).decode()}
print(lender_client.invokefunction('registerRental', [wallet_scripthash, test_nopht_d_hash, 68, 1, 5, 7, True]))
