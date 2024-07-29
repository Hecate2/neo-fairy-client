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

fairy_session = 'debug'
client = FairyClient(target_url, wallet_address, with_print=True, fairy_session=fairy_session, signers=lender)
client.new_snapshots_from_current_system()
client.set_gas_balance(100_0000_0000)
test_nopht_d_hash = Hash160Str('0x9ffb143877c7a0776f3b0dc88f55c4ad16c689c6')
client.delete_debug_info(test_nopht_d_hash)
# test_nopht_d_hash = client.virutal_deploy_from_path('../NFTLoan/NophtD/bin/sc/TestNophtD.nef')
client.contract_scripthash = client.virutal_deploy_from_path('../NFTLoan/NFTLoan/bin/sc/NFTFlashLoan.nef')
print(client.contract_scripthash)
print(client.list_filenames_of_contract())
assert client.list_debug_info() == [client.contract_scripthash]

print(client.set_assembly_breakpoints(0))
print(client.set_assembly_breakpoints(3))
try:
    client.set_assembly_breakpoints(1)
except ValueError as e:
    print(e)
    pass
assert client.list_assembly_breakpoints() == [0, 3]

assert client.set_source_code_breakpoint('NFTLoan.cs', 88) == [{'filename': 'NFTLoan.cs', 'line': 88}]  # get => "NEPHRENT";
assert client.set_source_code_breakpoints(['NFTLoan.cs', 253]) == [{'filename': 'NFTLoan.cs', 'line': 253}]  # ExecutionEngine.Assert(externalTokenId.Length <= 64, "tokenId.Length > 64");
assert client.list_source_code_breakpoints() == [{'filename': 'NFTLoan.cs', 'line': 88}, {'filename': 'NFTLoan.cs', 'line': 253}]
print(method_info := client.get_method_by_instruction_pointer(3309))  # ExecutionEngine.Assert(externalTokenContract != Runtime.ExecutingScriptHash, "Cannot register rental for tokens issued by this contract");
assert 'RegisterRental' in method_info['id']

print(rpc_breakpoint := client.debug_function_with_session('registerRental', [wallet_scripthash, test_nopht_d_hash, 68, '\x01', 5, 7, True]))
print(rpc_breakpoint := client.debug_step_into())
# Went to code ByteString.cs line 31: "OpCode(OpCode.SIZE)" and back to NFTLoan.cs again
# and hit the source code breakpoint
assert rpc_breakpoint.break_reason == 'SourceCodeBreakpoint' and rpc_breakpoint.instruction_pointer == 3284
print(rpc_breakpoint := client.debug_step_over_assembly())
assert rpc_breakpoint.break_reason == 'None' and rpc_breakpoint.instruction_pointer == 3286
# print(rpc_breakpoint := client.debug_step_out())

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
assert client.previous_raw_result['result']['sourcefilename'] == 'Contract.cs'
assert client.previous_raw_result['result']['sourcelinenum'] == 42
assert 'Called Contract Does Not Exist' in client.previous_raw_result['result']['exception']
print(client.get_contract_opcode_coverage())
print(client.clear_contract_opcode_coverage())
for k, v in client.get_contract_opcode_coverage().items():
    assert v is False

print(client.delete_assembly_breakpoints(0))
print(client.delete_assembly_breakpoints())
print(client.delete_source_code_breakpoints(['NFTLoan.cs', 253]))
print(client.delete_source_code_breakpoints([]))
print(client.delete_debug_info(client.contract_scripthash))
print(client.delete_snapshots(fairy_session))
