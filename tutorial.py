from neo_fairy_client.rpc import FairyClient
from neo_fairy_client.utils import Hash160Str
target_url = 'http://127.0.0.1:16868'
wallet_address = 'Nb2CHYY5wTh2ac58mTue5S3wpG6bQv5hSY'
wallet_scripthash = Hash160Str.from_address(wallet_address)
client = FairyClient(fairy_session='Hello world! Your first contact with Fairy!',
                     wallet_address_or_scripthash=wallet_address,
                     auto_preparation=True)

nef_file, manifest = client.get_nef_and_manifest_from_path('../NFTLoan/NFTLoan/bin/sc/NFTFlashLoan.nef')
test_nopht_d_hash = client.virutal_deploy_from_path('../NFTLoan/NophtD/bin/sc/TestNophtD.nef')
anyupdate_short_safe_hash = client.virutal_deploy_from_path('../AnyUpdate/AnyUpdateShortSafe.nef')

client.invokefunction('putStorage', params=[0x02, 1])

import json
manifest_dict = json.loads(manifest)
manifest_dict['name'] = 'AnyUpdateShortSafe'
manifest = json.dumps(manifest_dict, separators=(',', ':'))
from neo_fairy_client.utils import Signer, WitnessScope
signer = Signer(wallet_scripthash, scopes=WitnessScope.Global)  # watch this!
print(
    client.invokefunction('anyUpdate', params=
    [nef_file, manifest, 'registerRental',
     [wallet_scripthash, test_nopht_d_hash, 68, 1, 5, 7, True]
    ],
    signers=signer)  # watch this!
)

client.copy_snapshot('Hello world! Your first contact with Fairy!', 'Cloned snapshot')
client.fairy_session = 'Cloned snapshot'  # selecting the new snapshot

b'''Debugging tutorial'''

with open('../NFTLoan/NFTLoan/bin/sc/NFTFlashLoan.nefdbgnfo', 'rb') as f:
    nefdbgnfo = f.read()
with open('../NFTLoan/NFTLoan/bin/sc/NFTFlashLoan.nef.txt', 'r') as f:
    dumpnef = f.read()
client.virutal_deploy_from_path('../NFTLoan/NFTLoan/bin/sc/NFTFlashLoan.nef', auto_set_debug_info=False)  # client.contract_scripthash is set
client.set_debug_info(nefdbgnfo, dumpnef)  # the debug info is by default registered for client.contract_scripthash

print(breakpoint := client.debug_function_with_session(  # do not invokefunction in debugging!
    'registerRental',
    params=[wallet_scripthash, test_nopht_d_hash, 68, 1, 5, 7, True],
    signers=None,  # Watch this! I wrote this on purpose
))