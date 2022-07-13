import json
from neo_test_client.rpc import TestClient
from neo_test_client.utils.types import Hash160Str, Signer, WitnessScope
from neo_test_client.utils.timers import gen_timestamp_and_date_str_in_seconds

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

with open('../AnyUpdate/AnyUpdateShortSafe.nef', 'rb') as f:
    anyupdate_nef_file = f.read()
with open('../AnyUpdate/AnyUpdateShortSafe.manifest.json', 'r') as f:
    anyupdate_manifest = f.read()

with open('../NFTLoan/NophtD/bin/sc/TestNophtD.nef', 'rb') as f:
    test_nopht_d_nef = f.read()
with open('../NFTLoan/NophtD/bin/sc/TestNophtD.manifest.json', 'r') as f:
    test_nopht_d_manifest = f.read()

with open('../NFTLoan/NFTLoan/bin/sc/NFTFlashLoan.nef', 'rb') as f:
    nef_file = f.read()
with open('../NFTLoan/NFTLoan/bin/sc/NFTFlashLoan.manifest.json', 'r') as f:
    manifest_dict = json.loads(f.read())
    manifest_dict['name'] = 'AnyUpdateShortSafe'
    manifest = json.dumps(manifest_dict, separators=(',', ':'))

FAULT_MESSAGE = 'ASSERT is executed with false result.'

rpc_server_session = 'NophtD'
lender_client = TestClient(target_url, wallet_address, wallet_path, wallet_password, rpc_server_session=rpc_server_session, signer=lender, with_print=True)
borrower_client = TestClient(target_url, borrower_address, borrower_wallet_path, wallet_password, rpc_server_session=rpc_server_session, signer=borrower, with_print=True)
lender_client.open_fairy_wallet()
print('#### CHECKLIST BEFORE TEST')
print(lender_client.delete_snapshots(lender_client.list_snapshots()))
print(lender_client.new_snapshots_from_current_system())
print(lender_client.list_snapshots())
print(lender_client.set_gas_balance(100_0000_0000))
print(borrower_client.set_gas_balance(100_0000_0000))
print(lender_client.set_neo_balance(100))
print(borrower_client.set_neo_balance(100))
assert lender_client.get_neo_balance() == borrower_client.get_neo_balance() == 100
print(initial_lender_gas := lender_client.get_gas_balance())
print(initial_borrower_gas := borrower_client.get_gas_balance())
assert initial_lender_gas == initial_borrower_gas == 100_0000_0000
print('#### END CHECKLIST')

anyupdate_short_safe_hash = lender_client.virtual_deploy(anyupdate_nef_file, anyupdate_manifest)
test_nopht_d_hash = lender_client.virtual_deploy(test_nopht_d_nef, test_nopht_d_manifest)
lender_client.contract_scripthash = anyupdate_short_safe_hash
borrower_client.contract_scripthash = anyupdate_short_safe_hash

lender_client.invokefunction('putStorage', params=[0x02, 1])


def query_all_rental(client=lender_client, external_token_id=1, internal_token_id=1, timestamp: int = None):
    print(f'client rpc session: {client.rpc_server_session}')
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
    print(getRegisteredRentalByToken := client.invokefunction('anyUpdate', params=[nef_file, manifest, 'getRegisteredRentalByToken', [anyupdate_short_safe_hash, internal_token_id, wallet_scripthash]]))
    print('====listRegisteredRentalByRenter')
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listRegisteredRentalByRenter', [wallet_scripthash]]))
    print('external token')
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listRegisteredRentalByRenter', [wallet_scripthash, test_nopht_d_hash]]))
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'getRegisteredRentalByRenter', [wallet_scripthash, test_nopht_d_hash, external_token_id]]))
    print('internal token')
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listRegisteredRentalByRenter', [wallet_scripthash, anyupdate_short_safe_hash]]))
    print(getRegisteredRentalByRenter := client.invokefunction('anyUpdate', params=[nef_file, manifest, 'getRegisteredRentalByRenter', [wallet_scripthash, anyupdate_short_safe_hash, internal_token_id]]))
    assert getRegisteredRentalByToken == getRegisteredRentalByRenter
    print('====listRentalDeadlineByRenter')
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listRentalDeadlineByRenter', []]))
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listRentalDeadlineByRenter', [wallet_scripthash]]))
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listRentalDeadlineByRenter', [wallet_scripthash, internal_token_id]]))
    print(listRentalDeadlineByRenter := client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listRentalDeadlineByRenter', [wallet_scripthash, internal_token_id, borrower_scripthash]]))
    if timestamp:
        print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'getRentalDeadlineByRenter', [wallet_scripthash, internal_token_id, borrower_scripthash, timestamp]]))
    print('====listRentalDeadlineByTenant')
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listRentalDeadlineByTenant', []]))
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listRentalDeadlineByTenant', [borrower_scripthash]]))
    print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listRentalDeadlineByTenant', [borrower_scripthash, internal_token_id]]))
    print(listRentalDeadlineByTenant := client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listRentalDeadlineByTenant', [borrower_scripthash, internal_token_id, wallet_scripthash]]))
    if timestamp:
        print(client.invokefunction('anyUpdate', params=[nef_file, manifest, 'getRentalDeadlineByTenant', [borrower_scripthash, internal_token_id, wallet_scripthash, timestamp]]))
    assert listRentalDeadlineByRenter == listRentalDeadlineByTenant
    client.with_print, client.function_default_relay = with_print, function_default_relay


print(lender_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'registerRental', [wallet_scripthash, test_nopht_d_hash, 68, 1, 5, 7, True]]))
print(lender_client.totalfee, lender_client.previous_system_fee, lender_client.previous_network_fee)
query_all_rental()
print(lender_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'registerRental', [wallet_scripthash, test_nopht_d_hash, 32, 1, 10, 7, True]]))
print(lender_client.totalfee, lender_client.previous_system_fee, lender_client.previous_network_fee)
print(lender_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'setRentalPrice', [wallet_scripthash, test_nopht_d_hash, 1, 10]]))
print(lender_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'setRentalPrice', [wallet_scripthash, anyupdate_short_safe_hash, 1, 3]]))
assert lender_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'registerRental', [wallet_scripthash, test_nopht_d_hash, 1, 1, 5, 7, True]], do_not_raise_on_result=True) == FAULT_MESSAGE
query_all_rental()
print(lender_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listExternalTokenInfo', [0]]))
print(lender_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listExternalTokenInfo', [1]]))
print(lender_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'getExternalTokenInfo', [1]]))
print(lender_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listInternalTokenId', [test_nopht_d_hash]]))
print(lender_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listInternalTokenId', [test_nopht_d_hash, 0]]))
print(lender_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'listInternalTokenId', [test_nopht_d_hash, 1]]))
print(lender_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'getInternalTokenId', [test_nopht_d_hash, 1]]))

borrow_timestamp, _ = gen_timestamp_and_date_str_in_seconds(0)
lender_client.set_snapshot_timestamp(borrow_timestamp, rpc_server_session)

rpc_session_correct_payback = rpc_server_session + " borrow"
borrower_client.copy_snapshot(rpc_server_session, rpc_session_correct_payback)
borrower_client.rpc_server_session = rpc_session_correct_payback
lender_client.rpc_server_session = rpc_session_correct_payback
rental_period = 16000
print(execution_timestamp := borrower_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'borrow', [wallet_scripthash, borrower_scripthash, 15, 1, rental_period]]))
assert execution_timestamp == borrow_timestamp
# cannot borrow the same token from the same owner twice in a single block
assert FAULT_MESSAGE == borrower_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'borrow', [wallet_scripthash, borrower_scripthash, 10, test_nopht_d_hash, 1, rental_period]], do_not_raise_on_result=True)
assert 15 == borrower_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'balanceOf', [borrower_scripthash, 1]], relay=False)
print('GAS consumption:', initial_borrower_gas - borrower_client.get_gas_balance())
query_all_rental(client=borrower_client, timestamp=borrow_timestamp)

borrow_timestamp2 = borrow_timestamp + 100
borrower_client.set_snapshot_timestamp(borrow_timestamp2, rpc_session_correct_payback)
assert borrow_timestamp2 == borrower_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'borrow', [wallet_scripthash, borrower_scripthash, 30, test_nopht_d_hash, 1, rental_period - 100]])
# cannot borrow an amount <= 0
assert FAULT_MESSAGE == borrower_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'borrow', [wallet_scripthash, borrower_scripthash, 0, test_nopht_d_hash, 1, rental_period - 100]], do_not_raise_on_result=True)
assert FAULT_MESSAGE == borrower_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'borrow', [wallet_scripthash, borrower_scripthash, -1, test_nopht_d_hash, 1, rental_period - 100]], do_not_raise_on_result=True)
# cannot borrow more than total supply
assert FAULT_MESSAGE == borrower_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'borrow', [wallet_scripthash, borrower_scripthash, 56, test_nopht_d_hash, 1, rental_period - 100]], do_not_raise_on_result=True)
# we borrowed 15 tokens at borrow_timestamp and 30 tokens at borrow_timestamp2
# both will expire at borrow_timestamp + rental_period
assert 45 == borrower_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'balanceOf', [borrower_scripthash, 1]], relay=False)
print('GAS consumption:', initial_borrower_gas - borrower_client.get_gas_balance())
query_all_rental(client=borrower_client, timestamp=borrow_timestamp2)

print(borrower_client.get_gas_balance(owner=anyupdate_short_safe_hash))
payback_timestamp = borrow_timestamp + rental_period
assert borrower_client.get_gas_balance() - initial_borrower_gas == -300  # 100*2 rental price + 50*2 collateral
assert borrower_client.get_gas_balance(owner=anyupdate_short_safe_hash) == 100
print(borrower_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'payback', [wallet_scripthash, borrower_scripthash, test_nopht_d_hash, 1, borrow_timestamp, borrower_scripthash, False]]))
assert borrower_client.get_nep11token_balance(test_nopht_d_hash, 1, owner=anyupdate_short_safe_hash) == 100
assert FAULT_MESSAGE == lender_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'payback', [wallet_scripthash, borrower_scripthash, test_nopht_d_hash, 1, borrow_timestamp2, wallet_scripthash, True]], do_not_raise_on_result=True)
assert borrower_client.get_gas_balance() - initial_borrower_gas == -250  # +50 collateral
query_all_rental()

rpc_session_loan_expired = rpc_server_session + " payback expired"
borrower_client.copy_snapshot(rpc_session_correct_payback, rpc_session_loan_expired)
borrower_client.rpc_server_session = rpc_session_loan_expired
lender_client.rpc_server_session = rpc_session_loan_expired
borrower_client.set_snapshot_timestamp(payback_timestamp + 10, rpc_session_loan_expired)

print(lender_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'closeNextRental', [wallet_scripthash, 1, borrower_scripthash, borrow_timestamp2]]))
print(lender_client.totalfee, lender_client.previous_system_fee, lender_client.previous_network_fee)
assert '''Method "transfer" with 3 parameter(s) doesn't exist in the contract''' in borrower_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'payback', [wallet_scripthash, borrower_scripthash, test_nopht_d_hash, 1, borrow_timestamp2, borrower_scripthash, False]], do_not_raise_on_result=True)
query_all_rental(timestamp=borrow_timestamp2)
lender_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'payback', [wallet_scripthash, borrower_scripthash, test_nopht_d_hash, 1, borrow_timestamp2, wallet_scripthash, True]])
print(lender_client.totalfee, lender_client.previous_system_fee, lender_client.previous_network_fee)
r'''
In order to compute network fee at a different timestamp,
make sure your C# codes of your Fairy plugin has persistingBlock assigned for MakeTransaction
'''
query_all_rental()
assert lender_client.get_nep11token_balance(test_nopht_d_hash, 1) == 30
assert lender_client.get_nep11token_balance(test_nopht_d_hash, 1, owner=anyupdate_short_safe_hash) == 70
assert lender_client.get_gas_balance() - initial_lender_gas == 250  # 2*100 rental price + 50 collateral

assert '''Method "transfer" with 3 parameter(s) doesn't exist in the contract''' in lender_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'unregisterRental', [wallet_scripthash, test_nopht_d_hash, 70, 1, False]], do_not_raise_on_result=True)
assert [] == lender_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'flashBorrowDivisible', [wallet_scripthash, test_nopht_d_hash, 1, Hash160Str.zero(), 70, anyupdate_short_safe_hash, 'listRentalDeadlineByTenant', []]])
assert [] == lender_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'flashBorrowDivisible', [wallet_scripthash, test_nopht_d_hash, 1, wallet_scripthash, 70, anyupdate_short_safe_hash, 'listRentalDeadlineByTenant', []]])
assert FAULT_MESSAGE == lender_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'flashBorrowDivisible', [wallet_scripthash, test_nopht_d_hash, 1, wallet_scripthash, 71, anyupdate_short_safe_hash, 'listRentalDeadlineByTenant', []]], do_not_raise_on_result=True)
assert FAULT_MESSAGE == lender_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'flashBorrowDivisible', [wallet_scripthash, test_nopht_d_hash, 1, Hash160Str.zero(), 71, anyupdate_short_safe_hash, 'listRentalDeadlineByTenant', []]], do_not_raise_on_result=True)
assert 0 == lender_client.invokefunction('anyUpdate', params=[nef_file, manifest, 'unregisterRental', [wallet_scripthash, test_nopht_d_hash, 70, 1, True]])
