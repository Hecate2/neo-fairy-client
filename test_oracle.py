import base64
from neo_fairy_client.rpc import TestClient
from neo_fairy_client.utils.types import Hash160Str, Signer, WitnessScope
from neo_fairy_client.utils.interpreters import Interpreter

target_url = 'http://127.0.0.1:16868'
wallet_address = 'Nb2CHYY5wTh2ac58mTue5S3wpG6bQv5hSY'
wallet_scripthash = Hash160Str.from_address(wallet_address)
wallet_path = 'testnet.json'
wallet_password = '1'

with open('../neo-fairy-oracle/oracle-demo/bin/sc/oracle-demo.nef', 'rb') as f:
    nef_file = f.read()
with open('../neo-fairy-oracle/oracle-demo/bin/sc/oracle-demo.manifest.json', 'r') as f:
    manifest = f.read()
with open('../neo-fairy-oracle/oracle-demo/bin/sc/oracle-demo.nefdbgnfo', 'rb') as f:
    nefdbgnfo = f.read()
with open('../neo-fairy-oracle/oracle-demo/bin/sc/oracle-demo.nef.txt', 'r') as f:
    dumpnef = f.read()

rpc_server_session = 'oracle'
client = TestClient(target_url, wallet_address, wallet_path, wallet_password, rpc_server_session=rpc_server_session, with_print=True)

client.open_fairy_wallet()

client.delete_snapshots(client.list_snapshots())
client.new_snapshots_from_current_system()
client.set_gas_balance(100_0000_0000)
client.contract_scripthash = client.virtual_deploy(nef_file, manifest)
print(client.contract_scripthash)

# client.set_debug_info(nefdbgnfo, dumpnef)
# client.set_assembly_breakpoints(65)
#
# print(client.debug_function_with_session('createRequest', ['https://www.binance.com/api/v3/ticker/price?symbol=NEOUSDT', 'price', 'callback', 'testUserData', 1_0000_0000]))
# print(client.debug_step_over_assembly())
# print(client.debug_continue())

result = client.invokefunction('createRequest', ['https://www.binance.com/api/v3/ticker/price?symbol=NEOUSDT', 'price', 'callback', 'testUserData', 1_0000_0000])
print(client.previous_raw_result['result']['oraclerequests'])
