from neo_fairy_client.rpc import FairyClient
from neo_fairy_client.utils.types import Hash160Str

target_url = 'http://127.0.0.1:16868'
flamingo_swap_factory = Hash160Str('0xca2d20610d7982ebe0bed124ee7e9b2d580a6efc')
flamingo_swap_router = Hash160Str('0xf970f4ccecd765b63732b821775dc38c25d74f23')
bneo = Hash160Str('0x48c40d4666f93408be1bef038b6722404d9a4c2a')  # decimal 8
gas = Hash160Str('0xd2a4cff31913016155e38e474a2c06d08be276cf')  # decimal 8
fusdt = Hash160Str('0xcd48b160c1bbc9d74997b803b9a7ad50a4bef020')  # decimal 6

client = FairyClient(target_url, function_default_relay=False, script_default_relay=False)
client.contract_scripthash = flamingo_swap_router
# print(swap_pairs := client.invokefunction_of_any_contract(flamingo_swap_factory, 'getAllExchangePair', []))
# print(swap_pairs := client.invokefunction_of_any_contract(flamingo_swap_factory, 'getExchangePair', [gas, fusdt]))
print(bneo_price := client.invokefunction('getAmountsOut', [1_0000_0000, [bneo, fusdt]]))
print(client.previous_raw_result['result']['script'])
print(gas_price := client.invokefunction('getAmountsOut', [1_0000_0000, [gas, bneo, fusdt]]))
print(client.previous_raw_result['result']['script'])
