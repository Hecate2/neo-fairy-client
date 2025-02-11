import base64

import neo_fairy_client
from neo_fairy_client.rpc import FairyClient
from neo_fairy_client.utils.types import Hash160Str, Signer, WitnessScope
from neo_fairy_client.utils.interpreters import Interpreter
from neo_fairy_client.utils.oracle import OracleRequest

target_url = 'http://127.0.0.1:16868'
wallet_address = 'Nb2CHYY5wTh2ac58mTue5S3wpG6bQv5hSY'
wallet_scripthash = Hash160Str.from_address(wallet_address)

fairy_session = 'oracle'
client = FairyClient(target_url, wallet_address, fairy_session=fairy_session, with_print=True)

client.delete_snapshots(client.list_snapshots())
client.new_snapshots_from_current_system()
client.set_gas_balance(100_0000_0000)
scripthash = client.virutal_deploy_from_path('../neo-fairy-oracle/oracle-demo/bin/sc/OracleDemo.nef')
r"""
using System.Numerics;
using Neo.SmartContract.Framework;
using Neo.SmartContract.Framework.Native;
using Neo.SmartContract.Framework.Services;
namespace oracle_demo
{
    public class OracleDemo : SmartContract
    {
        private static readonly ByteString PREFIX_COUNT = "\xcc";
        private static readonly ByteString PREFIX_DATA = "\xdd";
        public static string GetRequestData() => Storage.Get(PREFIX_DATA);
        public static BigInteger GetRequestCount() => (BigInteger)Storage.Get(PREFIX_COUNT);
        public static void CreateRequest(string url, string filter, string callback, byte[] userData, long gasForResponse) => Oracle.Request(url, filter, callback, userData, gasForResponse);
        public static void Callback(string url, byte[] userData, int code, ByteString result)
        {
            ExecutionEngine.Assert(Runtime.CallingScriptHash == Oracle.Hash, "Unauthorized!");
            StorageContext currentContext = Storage.CurrentContext;
            result = ((ByteString[])StdLib.JsonDeserialize(result))[0];
            Storage.Put(currentContext, PREFIX_DATA, result);
            Storage.Put(currentContext, PREFIX_COUNT,
                (BigInteger)Storage.Get(currentContext, PREFIX_COUNT) + 1);
        }
    }
}
"""
print(client.contract_scripthash)

# client.set_debug_info(nefdbgnfo, dumpnef)
# client.set_assembly_breakpoints(65)
#
# print(client.debug_function_with_session('createRequest', ['https://www.binance.com/api/v3/ticker/price?symbol=NEOUSDT', 'price', 'callback', 'testUserData', 1_0000_0000]))
# print(client.debug_step_over_assembly())
# print(client.debug_continue())

assert client.invokefunction('getRequestCount') == 0
result = client.invokefunction('createRequest', ['https://www.binance.com/api/v3/ticker/price?symbol=NEOUSDT', '$.price', 'callback', 'testUserData', 1_0000_0000])
print(client.previous_raw_result['result']['oraclerequests'])
oracle_request: OracleRequest = OracleRequest(client.previous_raw_result['result']['oraclerequests'][0])
# client.delete_assembly_breakpoints()
# client.set_assembly_breakpoints(60)
# print(client.oracle_finish(base64.b64encode("10.51000000".encode()), oracle_request_id=oracle_request.request_id, debug=True))
raw_response = r'''{"symbol":"NEOUSDT","price":"10.51000000"}'''
filtered_response = client.oracle_json_path(raw_response, oracle_request.filter)
assert filtered_response == b'["10.51000000"]'
print(client.oracle_finish(filtered_response, oracle_request_id=oracle_request.request_id, debug=False))
print(client.invokefunction('getRequestData'))
assert "10.51000000" == client.invokefunction('getRequestData', with_print=False)
assert client.invokefunction('getRequestCount') == 1