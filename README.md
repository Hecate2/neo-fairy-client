Non-official test suite inherited from https://github.com/Hecate2/neo-ruler/ , in Python.

Features comply with https://github.com/Hecate2/neo-rpc-server-with-session/ .

A crude JavaScript version is available at https://github.com/Hecate2/neo-fairy-gate/blob/master/src/libs/NeoFairyClient.jsx .

#### Tutorial for testing

`pip install neo-fairy-client` or `py -m build && cd dist && pip install neo_fairy_client***.whl`. The only dependency is `requests`.

**Python >= 3.8 required!** Some steps in this tutorial is to help you understand the details about how Fairy works. In actual combat, you can read the source codes of `FairyClient` and enjoy many automatic conveniences that Fairy offers. 

##### Extremely fast version:

Let's simply simulate transactions collateralizing NEO to neoburger, and then redeeming them. Remember to launch [neo-fairy-test](https://github.com/Hecate2/neo-fairy-test/) at http://localhost:16868 before you start.

```python
from neo_fairy_client import FairyClient, defaultFairyWalletScriptHash, NeoAddress, GasAddress

bneo = 0x48c40d4666f93408be1bef038b6722404d9a4c2a
c = FairyClient(target_url='http://localhost:16868', fairy_session='neoburger', contract_scripthash=bneo, wallet_address_or_scripthash=defaultFairyWalletScriptHash)
c.set_neo_balance(1_000, account=defaultFairyWalletScriptHash)
assert c.invokefunction_of_any_contract(NeoAddress, 'balanceOf', [defaultFairyWalletScriptHash]) == 1_000
c.invokefunction_of_any_contract(NeoAddress, 'transfer', [defaultFairyWalletScriptHash, bneo, 1000, None])
assert c.invokefunction('balanceOf', [defaultFairyWalletScriptHash]) == 1000_0000_0000  # calling bNEO balance
assert c.invokefunction_of_any_contract(NeoAddress, 'balanceOf', [defaultFairyWalletScriptHash]) == 0
result = c.invokefunction_of_any_contract(GasAddress, 'transfer', [defaultFairyWalletScriptHash, bneo, 1_0000_0000, None])
print(result)
assert c.invokefunction('balanceOf', [defaultFairyWalletScriptHash]) == 0
assert c.invokefunction_of_any_contract(NeoAddress, 'balanceOf', [defaultFairyWalletScriptHash]) == 1_000
```

Then let's also try testing and debugging some local contracts. You can go to https://github.com/neo-project/neo-devpack-dotnet/tree/master/examples/Example.SmartContract.SampleRoyaltyNEP11Token for an example contract `SampleRoyaltyNEP11Token`. Remember to compile your contract with `nccs Example.SmartContract.SampleRoyaltyNEP11Token.csproj --debug --assembly --optimize=All`. The `--debug` flag gives a debug info file with suffix `.nefdbgnfo`. neo-fairy-client utilizes this file automatically for debugging.

```python
from neo_fairy_client import FairyClient, defaultFairyWalletScriptHash, Signer

c = FairyClient(target_url='http://localhost:16868', fairy_session='mint_multiple', signers=Signer(defaultFairyWalletScriptHash))
c.set_snapshot_checkwitness(True)  # so that all CheckWitness returns True
c.virutal_deploy_from_path(r'./bin/sc/SampleRoyaltyNEP11Token.nef')
c.invokefunction('mint', [defaultFairyWalletScriptHash])
assert c.invokefunction('tokensOf', [defaultFairyWalletScriptHash]) == ['\x01']

c.set_snapshot_checkwitness(False)
assert 'No Authorization!' in c.invokefunction(
    'mint', [defaultFairyWalletScriptHash], do_not_raise_on_result=True)
# ExecutionEngine.Assert(IsOwner() || IsMinter(), "No Authorization!");
c.set_source_code_breakpoint('test-compiler.cs', 105)
b = c.debug_function_with_session('mint', [defaultFairyWalletScriptHash])
print(b)
print(c.debug_continue())  # FAULT because the authorized minter is not you
c.invokefunction('setMinter', [defaultFairyWalletScriptHash],
     signers=Signer("NUuJw4C4XJFzxAvSZnFTfsNoWZytmQKXQP"))  # pretend to be the authorized owner
assert c.invokefunction('getMinter') == defaultFairyWalletScriptHash
c.invokefunction('mint', [defaultFairyWalletScriptHash])
assert c.invokefunction('tokensOf', [defaultFairyWalletScriptHash]) == ['\x01', '\x02']
```

For your own complex tests, visit [test_nftloan.py](test_nftloan.py) as a more complex sample of usage. The tested contract can be found at https://github.com/Hecate2/NFTLoan . Contract `AnyUpdateShortSafe` is an old-fashioned contract for testing, deployed on testnet T4 (which has been deprecated; we now use testnet T5), with source codes at https://github.com/Hecate2/AnyUpdate/ . You can skip using `AnyUpdate` by calling the RPC method `virtualdeploy`. 

##### Step 1: Run a neo-cli with Fairy plugin!

Head to https://github.com/Hecate2/neo-fairy-test/ to prepare it. You do not really have to wait for the blocks to be completely synchronized. The plugin is an HTTP server that will help you interact with Neo.

##### Step 2: Using your client, prepare your server snapshot

Place a json file of neo wallet (assumed to be `testnet.json` with password `1`) beside `neo-cli.exe`, and call your Fairy server with the following Python codes: (Complete codes available at https://github.com/Hecate2/neo-fairy-client/blob/master/tutorial.py )

```python
from neo_fairy_client.rpc import FairyClient
from neo_fairy_client.utils import Hash160Str
target_url = 'http://127.0.0.1:16868'
wallet_address = 'Nb2CHYY5wTh2ac58mTue5S3wpG6bQv5hSY'
wallet_scripthash = Hash160Str.from_address(wallet_address)
wallet_path = 'testnet.json'
wallet_password = '1'
client = FairyClient(fairy_session='Hello world! Your first contact with Fairy!',
                     wallet_address_or_scripthash=wallet_address,
                     auto_preparation=True)
```

Here `auto_preparation=True` tries to delete the old snapshot on the Fairy server named `Hello world! Your first contact with Fairy!`, and creates a new snapshot of the same name based on the current Neo system snapshot, then opens the wallet on Fairy server and automatically sets you NEO and GAS balance both to 100 (*10^8). 

If you are planning to run a public Fairy server, you need to open the Fairy wallet so that users do not have to open it through RPC. I am also planning to remove wallet objects in Fairy service. 

#### Step 2.1: Mint billions of NEO and transfer them!

(Of course these are just fairy NEO in the memory of your imagination)

```python
from neo_fairy_client.utils import NeoAddress
client.set_neo_balance(1_000_000_000)
print(f"Your NEO balance: {client.invokefunction_of_any_contract(NeoAddress, 'balanceOf', [wallet_scripthash])}")
client.invokefunction_of_any_contract(NeoAddress, 'transfer', [wallet_scripthash, Hash160Str.zero(), 1_000_000_000, None])
print(f"NEO balance of zero address: {client.invokefunction_of_any_contract(NeoAddress, 'balanceOf', [Hash160Str.zero()])}")
```

```
Hello world! Your first contact with Fairy!::balanceOf[0xb1983fa2479a0c8e2beae032d2df564b5451b7a5] relay=None [{'account': '0xb1983fa2479a0c8e2beae032d2df564b5451b7a5', 'scopes': 'CalledByEntry', 'allowedcontracts': [], 'allowedgroups': [], 'rules': []}]
Your NEO balance: 1000000000
Hello world! Your first contact with Fairy!::transfer[0xb1983fa2479a0c8e2beae032d2df564b5451b7a5, 0x0000000000000000000000000000000000000000, 1000000000, None] relay=None [{'account': '0xb1983fa2479a0c8e2beae032d2df564b5451b7a5', 'scopes': 'CalledByEntry', 'allowedcontracts': [], 'allowedgroups': [], 'rules': []}]
Hello world! Your first contact with Fairy!::balanceOf[0x0000000000000000000000000000000000000000] relay=None [{'account': '0xb1983fa2479a0c8e2beae032d2df564b5451b7a5', 'scopes': 'CalledByEntry', 'allowedcontracts': [], 'allowedgroups': [], 'rules': []}]
NEO balance of zero address: 1000000000
```

##### Step 2.2: I just want to interact with the real mainnet and testnet...

**DO NOT** set the `fairy_session` string for your `FairyClient`, or set it to `None`. Fairy will play real transactions without fairy session. Set `function_default_relay=True` in `FairyClient` or `relay=True` in a single `invokefunction` to automatically relay the transaction. 

**BE CAREFUL**:  By default, Fairy does interact with the real blockchain and relay transactions. **Do not use a wallet with real assets when you just want a test!**

Sometimes you may want to actually relay something after fairy tests. In such cases, set `confirm_relay_to_blockchain=True` in `FairyClient` to prevent automatic relaying as the final safety belt. 

##### Step 3: Deploy your contract virtually

Get the tested contracts in my example through these repos:

https://github.com/Hecate2/AnyUpdate

https://github.com/Hecate2/NFTLoan/

and place them properly.

```python
nef_file, manifest = client.get_nef_and_manifest_from_path('../NFTLoan/NFTLoan/bin/sc/NFTFlashLoan.nef')
test_nopht_d_hash = client.virutal_deploy_from_path('../NFTLoan/NophtD/bin/sc/TestNophtD.nef')
anyupdate_short_safe_hash = client.virutal_deploy_from_path('../AnyUpdate/AnyUpdateShortSafe.nef')
```

`client.virutal_deploy_from_path` deploys the `.nef` and `.manifest.json` to the snapshot of your Fairy session. The snapshot is similar to a fork of the current blockchain, named by your session string. You can now access to the deployed contract through your snapshot, but not through the actual blockchain. 

In our case, we deployed `AnyUpdate` to be updated to any other contract, and `test_nopht_d` as a divisible NFT to be operated. Though you can continue deploying `NFTLoan` by yourself, we are now going to call `AnyUpdate` to perform all the actions the same as `NFTLoan`.

##### Step 4: Call your contracts!

By design, `NFTLoan` initializes its token ID to be 1. However, this is not performed by `AnyUpdate`. Therefore, we first ask `AnyUpdate` to prepare the storage environment:

```python
client.invokefunction('putStorage', params=[0x02, 1])
```

Here we did not explicitly indicate the address of the called contract. This is because `client.virutal_deploy_from_path` has set `client.contract_scripthash` to be the address of the just deployed contract in the previous step.

Also notice that we should always put some string in `client.fairy_session`. If `fairy_session` is set to `None`, the client will (by my design) directly interact with the real blockchain, and write real transactions. 

##### Step 5: The storage written by Fairy is always valid in the same snapshot

```python
import json
manifest_dict = json.loads(manifest)
manifest_dict['name'] = 'AnyUpdateShortSafe'
manifest = json.dumps(manifest_dict, separators=(',', ':'))
print(
    client.invokefunction('anyUpdate', params=
    [nef_file, manifest, 'registerRental',
     [wallet_scripthash, test_nopht_d_hash, 68, 1, 5, 7, True]
    ]
    )
)
```

Extremely complex, huh? Not really. 

In the first 4 lines we are changing the contract name of `NFTLoan` in its manifest. This is because the contract cannot change its name in an update. Then we are just calling `AnyUpdate` to update itself becoming our `NFTLoan`, and execute the method `registerRental`. 

And **happily we will see a lot of red alerts** ending with:

```
[0x5c1068339fae89eb1a743909d0213e1d99dc5dc9] AnyUpdateShortSafe: Transfer failed
```

**W**hiskey **T**ango **F**oxtrot? Well, by reading the codes, we can assume that we have forgotten to add proper witnesses (in other words, signatures) to our call (we are not going to explain how to make the assumption for now). But how to add signatures?

##### Step 6: Adding signatures to your call

Signatures are important elements in Neo blockchain to check whether the operation is really allowed by stakeholders. In smart contracts, you should always check the witness of the token holder before transferring his/her tokens to someone else. 

```python
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
```

For testing purposes, you can just use `WitnessScope.Global` to allow any contract the transfer the assets of `wallet_scripthash` freely. A good news is that Fairy does not actually check if your signatures are really signed by the wallet owner. You can use any scripthash in `Signer` **(does not have to be the scripthash of the wallet)**, and Fairy will always recognize it to be a valid signature. 

If everything goes well, your Fairy client should print:

```
Hello world! Your first contact with Fairy!::putStorage[2, 1] relay=True [{'account': '0xb1983fa2479a0c8e2beae032d2df564b5451b7a5', 'scopes': 'CalledByEntry', 'allowedcontracts': [], 'allowedgroups': [], 'rules': []}]
Hello world! Your first contact with Fairy!::anyUpdate[b'NEF3Neo.Compiler.CSharp 3.1.0\x00\x00\x00\x00...
68
```

##### Step 7: Cloning snapshots

By cloning snapshots, you are "forking the blockchain" from your old snapshot again. The written transactions in the old snapshot will be remembered in the new snapshot. 

```python
client.copy_snapshot('Hello world! Your first contact with Fairy!', 'Cloned snapshot')
client.fairy_session = 'Cloned snapshot'  # selecting the new snapshot
```

Now just select a snapshot continue to invoke more methods! Everything happening in the cloned snapshot will affect neither the real blockchain nor the old snapshot. 

##### Last step: Understanding the errors and fixing the bugs

We are not going to continue with the cloned snapshots, but explain the red error information given by Fairy. Head to [tutorial.py](tutorial.py) and comment out the line mentioned in Step 4:

```python
# client.invokefunction('putStorage', params=[0x02, 1])
```

And run the whole tutorial. You'll see confusing errors like this:

```
Hello world! Your first contact with Fairy!::anyUpdate[b'NEF3Neo.Compiler.CSharp 3.1.0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00...
{"jsonrpc":"2.0","method":"invokefunctionwithsession","params":["Hello world! Your first contact with Fairy!",true,"0x5c1068339fae89eb1a743909d0213e1d99dc5dc9","anyUpdate",[{"type":"ByteArray","value":"TkVG...
{'jsonrpc': '2.0', 'id': 1, 'result': {'script': 'ERcVEQBEDBSRizQfl9u4WOivUwoue4ci+vAEJwwUpbdRVEtW39Iy4OorjgyaR6I/mLEXwAwOcmVnaXN...
Traceback (most recent call last):
  File "C:/Users/RhantolkYtriHistoria/NEO/neo-test-client/tutorial.py", line 26, in <module>
    client.invokefunction('anyUpdate', params=
  File "C:\Users\RhantolkYtriHistoria\NEO\neo-test-client\neo_fairy_client\rpc\fairy_client.py", line 478, in invokefunction
    return self.invokefunction_of_any_contract(self.contract_scripthash, operation, params,
  File "C:\Users\RhantolkYtriHistoria\NEO\neo-test-client\neo_fairy_client\rpc\fairy_client.py", line 465, in invokefunction_of_any_contract
    result = self.meta_rpc_method(
  File "C:\Users\RhantolkYtriHistoria\NEO\neo-test-client\neo_fairy_client\rpc\fairy_client.py", line 224, in meta_rpc_method
    raise ValueError(result_result['traceback'])
ValueError:    at Neo.VM.ExecutionEngine.ExecuteInstruction(Instruction instruction) in C:\Users\RhantolkYtriHistoria\NEO\neo-vm\src\Neo.VM\ExecutionEngine.cs:line 1143
   at Neo.VM.ExecutionEngine.ExecuteNext() in C:\Users\RhantolkYtriHistoria\NEO\neo-vm\src\Neo.VM\ExecutionEngine.cs:line 1454
Invalid type for SIZE: Any
CallingScriptHash=0x5c1068339fae89eb1a743909d0213e1d99dc5dc9[AnyUpdateShortSafe]
CurrentScriptHash=0x5c1068339fae89eb1a743909d0213e1d99dc5dc9[AnyUpdateShortSafe]
EntryScriptHash=0xb493e9d3b67262ba1f35dfc85dbfe6464c83c092
   at Neo.VM.ExecutionEngine.ExecuteInstruction(Instruction instruction) in C:\Users\RhantolkYtriHistoria\NEO\neo-vm\src\Neo.VM\ExecutionEngine.cs:line 1143
   at Neo.VM.ExecutionEngine.ExecuteNext() in C:\Users\RhantolkYtriHistoria\NEO\neo-vm\src\Neo.VM\ExecutionEngine.cs:line 1454
InstructionPointer=3532, OpCode SIZE, Script Length=8518
InstructionPointer=3814, OpCode DUP, Script Length=8518
InstructionPointer=4574, OpCode STLOC3, Script Length=8518
InstructionPointer=502, OpCode STLOC2, Script Length=3194
InstructionPointer=21384, OpCode , Script Length=21384
```

Now pay attention to the `InstructionPointer` stacks at last, especially the first line of the `InstructionPointer`s. By reading `NFTFlashLoan.nef.txt` (available in NFTLoan repository releases) created by `Dumpnef`, you'll get the following information near `InstructionPointer=3532`:

```
# Code NFTLoan.cs line 141: "ExecutionEngine.Assert(id.Length < 0xFD, "Too long id");"
3518 PUSHDATA1 54-6F-6F-20-6C-6F-6E-67-20-69-64 # as text: "Too long id"
3531 LDLOC2
3532 SIZE
3533 PUSHINT16 FD-00 # 253
3536 LT
3537 CALL_L 07-FB-FF-FF # pos: 2264, offset: -1273
```

And you can immediately locate the problem, finding that `id` is actually `null` and the operation `id.Length` is invalid. 

#### Tutorial for debugging

Still feeling difficult to locate bugs in testing? Just debug the contract with step-in, step-out and step-over. Prepare your debugging storage environment automatically with your test codes, set breakpoints on either source code lines or InstructionPointers of assembly codes, and watch all the values of variables based on their names! 

##### Step 0: Set debug info

Well... Thanks to the `auto_set_debug_info=True` option in `client.virutal_deploy_from_path`, Fairy has automatically registered the debug info of `AnyUpdate` and `TestNophtD` for you when you deployed them. But Fairy does not recognize the source codes of `NFTLoan` because we did not actually deploy it. Now we are going to set debug info manually. 

```python
with open('../NFTLoan/NFTLoan/bin/sc/NFTFlashLoan.nefdbgnfo', 'rb') as f:
    nefdbgnfo = f.read()
with open('../NFTLoan/NFTLoan/bin/sc/NFTFlashLoan.nef.txt', 'r') as f:
    dumpnef = f.read()
client.virutal_deploy_from_path('../NFTLoan/NFTLoan/bin/sc/NFTFlashLoan.nef', auto_set_debug_info=False)  # client.contract_scripthash is set
client.set_debug_info(nefdbgnfo, dumpnef)  # the debug info is by default registered for client.contract_scripthash
```

##### Step 1: Call a method in debug mode

Your debugging runtime storage environment is always inherited from a test session. It is recommended to build the debugging environment automatically with testing codes.

```python
print(breakpoint := client.debug_function_with_session(  # do not invokefunction in debugging!
    'registerRental',
    params=[wallet_scripthash, test_nopht_d_hash, 68, 1, 5, 7, True],
    signers=None,  # Watch this! I wrote this on purpose
))
```

With `signers=None` your Fairy client uses `CalledByEntry` signature, which is actually insufficient in our case. You should get the following to be printed

```
Cloned snapshot::debugfunction registerRental
RpcBreakpoint VMState.FAULT ExecutionEngine.cs line 33 instructionPointer 2281: Assert(false);
```

which directly leads you to the source code! Now you can easily figure out the signature problems.

If no fault occurs, you should get VMState.HALT in `breakpoint`.

Note that **all debugging executions write nothing to the snapshot!**

##### Step 2: Set breakpoints; step-in, step-out, step-over, and watch variable values

Head to [test_debug.py](test_debug.py) in this repo to learn these operations!