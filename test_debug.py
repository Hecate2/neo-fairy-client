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
with open('../NFTLoan/NFTLoan/bin/sc/NFTFlashLoan.debug.json', 'r') as f:
    nefdbgnfo = json.dumps(json.loads(f.read()), separators=(',', ':'))
with open('../NFTLoan/NFTLoan/bin/sc/NFTFlashLoan.nef.txt', 'r') as f:
    dumpnef = f.read()

rpc_server_session = 'debug'
client = TestClient(target_url, Hash160Str.zero(), wallet_address, wallet_path, wallet_password, with_print=True, rpc_server_session=rpc_server_session, signer=lender)
client.openwallet()
client.contract_scripthash = client.virtual_deploy(nef_file, manifest)
print(client.contract_scripthash)
print(client.delete_debug_info(client.contract_scripthash))
print(client.set_debug_info(nefdbgnfo, dumpnef))
print(client.list_filenames_of_contract())
assert client.list_debug_info() == [client.contract_scripthash]

print(client.set_assembly_breakpoints(0))
print(client.set_assembly_breakpoints(3))
try:
    client.set_assembly_breakpoints(1)
except ValueError as e:
    print(e)
    pass
print(client.list_assembly_breakpoints())

print(client.set_source_code_breakpoint('NFTLoan.cs', 84))
print(client.set_source_code_breakpoints(['DivisibleNep11Token.cs', 100, 'TokenContract.cs', 30]))
print(client.set_source_code_breakpoints(['NFTLoan.cs', 242]))
print(client.list_source_code_breakpoints())

breakpoint_ = client.debug_function_with_session('registerRental', [wallet_scripthash, test_nopht_d_hash, 68, 1, 5, 7, True])
print(breakpoint_)
breakpoint_ = client.debug_continue()
print(breakpoint_)

print(client.delete_assembly_breakpoints(0))
print(client.delete_assembly_breakpoints())
print(client.delete_source_code_breakpoints(['DivisibleNep11Token.cs', 100]))
print(client.delete_source_code_breakpoints([]))
print(client.delete_debug_info(client.contract_scripthash))
