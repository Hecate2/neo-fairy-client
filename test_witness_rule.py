from neo_fairy_client import FairyClient, Signer, WitnessScope, Hash160Str
from neo_fairy_client.utils.WitnessRule import *

wallet_address = 'Nb2CHYY5wTh2ac58mTue5S3wpG6bQv5hSY'
wallet_scripthash = Hash160Str.from_address(wallet_address)

client = FairyClient(fairy_session='test-witness-rule', wallet_address_or_scripthash=wallet_address, with_print=False)
nftloan_scripthash = client.virutal_deploy_from_path('../NFTLoan/NFTLoan/bin/sc/NFTFlashLoan.nef')
test_nopht_d_hash = client.virutal_deploy_from_path('../NFTLoan/NophtD/bin/sc/TestNophtD.nef')
client.contract_scripthash = nftloan_scripthash
print(client.contract_scripthash)
correct_signer = [Signer(wallet_address, WitnessScope.WitnessRules,
                         rules=Allow(
                             Or(
                                 And(CalledByEntry(), ScriptHash(nftloan_scripthash)),  # me calling nftloan
                                 And(CalledByContract(nftloan_scripthash), ScriptHash(test_nopht_d_hash))  # nftloan calling nophtd
                             )
                         )
                         )]
client.signers = correct_signer
print(client.invokefunction('registerRental', [wallet_scripthash, test_nopht_d_hash, 68, 1, 5, 7, True]))
print(client.totalfee, client.previous_system_fee, client.previous_network_fee)
wrong_signer = [Signer(wallet_address, WitnessScope.WitnessRules,
                         rules=Deny(
                             Or(
                                 And(CalledByEntry(), ScriptHash(nftloan_scripthash)),  # me calling nftloan
                                 And(CalledByContract(nftloan_scripthash), ScriptHash(test_nopht_d_hash))  # nftloan calling nophtd
                             )
                         )
                         )]
client.signers = wrong_signer
assert client.invokefunction('registerRental', [wallet_scripthash, test_nopht_d_hash, 32, 1, 10, 7, True], do_not_raise_on_result=True)
client.signers = correct_signer
print(client.invokefunction('registerRental', [wallet_scripthash, test_nopht_d_hash, 32, 1, 10, 7, True]))
print(client.totalfee, client.previous_system_fee, client.previous_network_fee)
print(client.invokefunction('setRentalPrice', [wallet_scripthash, test_nopht_d_hash, 1, 10]))
print(client.invokefunction('setRentalPrice', [wallet_scripthash, nftloan_scripthash, 1, 3]))
assert client.invokefunction('registerRental', [wallet_scripthash, test_nopht_d_hash, 1, 1, 5, 7, True], do_not_raise_on_result=True)
print(client.invokefunction('listExternalTokenInfo', [0]))
print(client.invokefunction('listExternalTokenInfo', [1]))
print(client.invokefunction('getExternalTokenInfo', [1]))
print(client.invokefunction('listInternalTokenId', [test_nopht_d_hash]))
print(client.invokefunction('listInternalTokenId', [test_nopht_d_hash, 0]))
print(client.invokefunction('listInternalTokenId', [test_nopht_d_hash, 1]))
print(client.invokefunction('getInternalTokenId', [test_nopht_d_hash, 1]))
