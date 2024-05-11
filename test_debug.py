import json
from neo_fairy_client.rpc import FairyClient
from neo_fairy_client.utils.types import Hash160Str, Signer, WitnessScope
from neo_fairy_client import VMState

target_url = 'http://127.0.0.1:16868'
wallet_address = 'Nb2CHYY5wTh2ac58mTue5S3wpG6bQv5hSY'
wallet_scripthash = Hash160Str.from_address(wallet_address)

borrower_address = 'NaainHz563mJLsHRsPD4NrKjMEQGBXXJY9'
borrower_scripthash = Hash160Str.from_address(borrower_address)

lender = Signer(wallet_scripthash, scopes=WitnessScope.Global)
borrower = Signer(borrower_scripthash, scopes=WitnessScope.Global)

anyupdate_short_safe_hash = Hash160Str('0x5c1068339fae89eb1a743909d0213e1d99dc5dc9')  # AnyUpdate short safe
test_nopht_d_hash = Hash160Str('0x2a6cd301cad359fc85e42454217e51485fffe745')

with open('../NFTLoan/NFTLoan/bin/sc/NFTFlashLoan.nef', 'rb') as f:
    nef_file = f.read()
with open('../NFTLoan/NFTLoan/bin/sc/NFTFlashLoan.manifest.json', 'r') as f:
    manifest = f.read()
with open('../NFTLoan/NFTLoan/bin/sc/NFTFlashLoan.nefdbgnfo', 'rb') as f:
    nefdbgnfo = f.read()
with open('../NFTLoan/NFTLoan/bin/sc/NFTFlashLoan.nef.txt', 'r') as f:
    dumpnef = f.read()

fairy_session = 'debug'
client = FairyClient(target_url, wallet_address, with_print=True, fairy_session=fairy_session, signers=lender)
client.new_snapshots_from_current_system()
client.set_gas_balance(100_0000_0000)
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
print(client.get_method_by_instruction_pointer(4384))

print(client.debug_function_with_session('registerRental', [wallet_scripthash, test_nopht_d_hash, 68, '\x01', 5, 7, True]))
print(client.debug_step_into())
print(client.debug_step_out())
print(client.debug_step_over_assembly())

print(client.get_local_variables())
print(client.get_arguments())
print(client.get_static_fields())
print(client.get_evaluation_stack())
print(client.get_instruction_pointer())
print(client.get_variable_value_by_name("flashLoanPrice"))
print(client.get_variable_names_and_values())

print(client.debug_step_over())
print(rpc_breakpoint := client.debug_step_over_source_code())
assert rpc_breakpoint.state == VMState.BREAK
print(rpc_breakpoint := client.debug_continue())
assert rpc_breakpoint.state == VMState.FAULT  # we did not deployed NophtD here
assert client.previous_raw_result['result']['sourcefilename'] == 'NFTLoan.cs'
assert client.previous_raw_result['result']['sourcelinenum'] == 247
assert 'Called Contract Does Not Exist' in client.previous_raw_result['result']['exception']
print(client.get_contract_opcode_coverage())
print(client.clear_contract_opcode_coverage())
for k, v in client.get_contract_opcode_coverage().items():
    assert v is False

print(client.delete_assembly_breakpoints(0))
print(client.delete_assembly_breakpoints())
print(client.delete_source_code_breakpoints(['DivisibleNep11Token.cs', 100]))
print(client.delete_source_code_breakpoints([]))
print(client.delete_debug_info(client.contract_scripthash))
print(client.delete_snapshots(fairy_session))
