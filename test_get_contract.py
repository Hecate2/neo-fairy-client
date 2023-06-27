from neo_fairy_client.rpc.fairy_client import FairyClient, ManagementAddress, Hash160Str

client = FairyClient(function_default_relay=False)
print(result := client.invokefunction_of_any_contract(ManagementAddress, 'getContract', [Hash160Str("0xef4073a0f2b305a38ec4050e4d3d28bc40ea63f5")]))
print(result_fairy_contract := client.get_contract(Hash160Str("0xef4073a0f2b305a38ec4050e4d3d28bc40ea63f5")))