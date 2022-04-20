import string
import json
import os
from functools import partial
from typing import List, Union, Tuple, Any, Callable

from neo_test_client.utils.types import Hash160Str, Hash256Str, EngineResultInterpreter

from neo3 import vm, contracts, blockchain
from neo3.contracts import ApplicationEngine, interop
from neo3.contracts.native import NativeContract
from neo3.core import types
from neo3.core.types import UInt160
from neo3.network import payloads
from neo3.storage import StorageContext
from neo3.contracts import NeoToken, GasToken
neo, gas = NeoToken(), GasToken()

class TestEngine:
    NO_SIGNER = 'NO_SIGNER'
    Prefix_Account = 20
    Number_Prefix = b'\x04'
    
    @staticmethod
    def new_engine(previous_engine: ApplicationEngine = None) -> ApplicationEngine:
        tx = payloads.Transaction._serializable_init()
        if not previous_engine:
            blockchain.Blockchain.__it__ = None
            snapshot = blockchain.Blockchain(store_genesis_block=True).currentSnapshot  # blockchain is singleton
            return ApplicationEngine(contracts.TriggerType.APPLICATION, tx, snapshot, 0, test_mode=True)
        else:
            return ApplicationEngine(contracts.TriggerType.APPLICATION, tx, previous_engine.snapshot, 0, test_mode=True)
    
    @staticmethod
    def read_raw_nef_and_raw_manifest(nef_path: str, manifest_path: str = '') -> Tuple[bytes, dict]:
        with open(nef_path, 'rb') as f:
            raw_nef = f.read()
        if not manifest_path:
            file_path, fullname = os.path.split(nef_path)
            nef_name, _ = os.path.splitext(fullname)
            manifest_path = os.path.join(file_path, nef_name + '.manifest.json')
        with open(manifest_path, 'r') as f:
            raw_manifest = json.loads(f.read())
        return raw_nef, raw_manifest
    
    @staticmethod
    def build_nef_and_manifest_from_raw(raw_nef: bytes, raw_manifest: dict) \
            -> Tuple[contracts.NEF, contracts.manifest.ContractManifest]:
        nef = contracts.NEF.deserialize_from_bytes(raw_nef)
        manifest = contracts.manifest.ContractManifest.from_json(raw_manifest)
        return nef, manifest
    
    @property
    def state(self):
        return self.previous_engine.state
    
    @property
    def snapshot(self):
        return self.previous_engine.snapshot
    
    @property
    def snapshot_storage(self):
        return self.snapshot.storages._db.db['storages']
    
    @property
    def snapshot_contracts(self):
        return self.snapshot.storages._db.db['contracts']
    
    @property
    def result_stack(self):
        return self.previous_engine.result_stack
    
    def __init__(self, nef_path: str, manifest_path: str = '', signers: List[Union[str, UInt160, payloads.Signer]] = None,
                 scope: payloads.WitnessScope = payloads.WitnessScope.GLOBAL):
        """
        Only the contract specified in __init__ can be tested. You can deploy more contracts to be called by the tested
        contract.
        """
        self.Prefix_Account_bytes = EngineResultInterpreter.int_to_bytes(self.Prefix_Account)
        self.raw_nef, self.raw_manifest = self.read_raw_nef_and_raw_manifest(nef_path, manifest_path)
        self.nef, self.manifest = self.build_nef_and_manifest_from_raw(self.raw_nef, self.raw_manifest)
        self.previous_engine: ApplicationEngine = self.new_engine()
        self.previous_processed_result = None
        self.contract = contracts.ContractState(0, self.nef, self.manifest, 0,
                                                types.UInt160.deserialize_from_bytes(self.raw_nef))
        self.next_contract_id = 1  # if you deploy more contracts in a same engine, the contracts must have different id
        self.previous_engine.snapshot.contracts.put(self.contract)
        self.deployed_contracts = [self.contract]
        if signers:
            signers = list(map(lambda signer:
                               self.signer_auto_checker(signer, scope),
                               signers))
            self.signers = signers
        else:
            self.signers = []

        # add methods to this class for users to call contract methods
        for method in self.manifest.abi.methods:
            method_name = method.name
            method_name_with_print = method_name + '_with_print'
            if hasattr(self, method_name) or hasattr(self, method_name_with_print):
                print(f'Warning: method {method_name} or {method_name_with_print} already exists in {self}')
            partial_function = partial(self.invoke_method, method_name)
            setattr(self, method_name, partial_function)
            partial_function_with_print = partial(self.invoke_method_with_print, method_name)
            setattr(self, method_name_with_print, partial_function_with_print)
    
    def deploy_another_contract(self, nef_path: str, manifest_path: str = '') -> UInt160:
        """
        these extra contracts can be called but cannot be tested
        """
        raw_nef, raw_manifest = self.read_raw_nef_and_raw_manifest(nef_path, manifest_path)
        nef, manifest = self.build_nef_and_manifest_from_raw(raw_nef, raw_manifest)
        contract_hash = types.UInt160.deserialize_from_bytes(raw_nef[-20:])
        contract = contracts.ContractState(self.next_contract_id, nef, manifest, 0,
                                           contract_hash)
        self.previous_engine.snapshot.contracts.put(contract)
        self.deployed_contracts.append(contract)
        self.next_contract_id += 1
        return contract_hash
    
    @staticmethod
    def param_auto_checker(param: Any) -> Any:
        type_param = type(param)
        if type_param is Hash160Str:
            return param.to_UInt160().to_array()
        if type_param is Hash256Str:
            return param.to_UInt256().to_array()
        elif type_param is str:
            hex_alphabet = set(string.hexdigits)
            # WARNING: a dangerous guess here
            if len(param) == 40 and set(param).issubset(hex_alphabet):
                return types.UInt160.from_string(param).to_array()
            elif len(param) == 42 and param.startswith('0x') and set(param[0:2]).issubset(hex_alphabet):
                return types.UInt160.from_string(param[2:]).to_array()
            else:
                return param
        elif type_param is UInt160:
            return param.to_array()
        elif type_param is int or type_param is bytes or type_param is bool or param is None:
            return param
        else:
            raise ValueError(f'Unable to handle param {param} with type {type_param}')
    
    @staticmethod
    def signer_auto_checker(signer: Union[str, UInt160, Hash160Str, payloads.Signer], scope: payloads.WitnessScope) -> payloads.Signer:
        type_signer = type(signer)
        if type_signer is str and len(signer) == 40:
            return payloads.Signer(types.UInt160.from_string(signer), scope)
        elif type_signer is payloads.Signer:
            return signer
        elif type_signer is UInt160:
            return payloads.Signer(signer, scope)
        elif type_signer is Hash160Str:
            return payloads.Signer(signer.to_UInt160(), scope)
        else:
            raise ValueError(f'Unable to handle signer {signer} with type {type_signer}')

    @staticmethod
    def contract_hash_auto_checker(contract_hash: Union[UInt160, Hash160Str, str]):
        type_contract_hash = type(contract_hash)
        if type_contract_hash is Hash160Str:
            return types.UInt160.from_string(str(contract_hash)[2:])
        elif type_contract_hash is str:
            if len(contract_hash) == 40:
                return types.UInt160.from_string(contract_hash)
            elif len(contract_hash) == 42 and contract_hash.startswith('0x'):
                return types.UInt160.from_string(contract_hash[2:])
            else:
                return contract_hash
        elif type_contract_hash is UInt160:
            return contract_hash

    def invoke_method(self, method: str, params: List = None, signers: List[Union[str, UInt160, payloads.Signer]] = None,
                      scope: payloads.WitnessScope = payloads.WitnessScope.GLOBAL,
                      engine: ApplicationEngine = None, with_print=False) -> ApplicationEngine:
        if with_print:
            return self.invoke_method_with_print(method, params, signers, scope, engine)
        return self.invoke_method_of_arbitrary_contract(self.contract.hash, method, params, signers, scope, engine)

    def invoke_method_with_print(self, method: str, params: List = None, signers: List[Union[str, UInt160, payloads.Signer]] = None,
                                 scope: payloads.WitnessScope = payloads.WitnessScope.GLOBAL,
                                 engine: ApplicationEngine = None, result_interpreted_as_hex=False,
                                 result_interpreted_as_iterator=False, further_interpreter:Callable = None) -> ApplicationEngine:
        if not signers:
            signers = self.signers
        print(f'invoke method {method}:')
        executed_engine = self.invoke_method(method, params, signers, scope, engine)
        if executed_engine.state == executed_engine.state.FAULT:
            print(f'engine fault from method "{method}":')
            print(executed_engine.exception_message)
        self.print_results(executed_engine, result_interpreted_as_hex, result_interpreted_as_iterator, further_interpreter)
        return executed_engine

    def invoke_method_of_arbitrary_contract(self, contract_hash: Union[UInt160, Hash160Str, str], method: str, params: List = None,
                      signers: List[Union[str, UInt160, payloads.Signer]] = None,
                      scope: payloads.WitnessScope = payloads.WitnessScope.GLOBAL,
                      engine: ApplicationEngine = None):
        if params is None:
            params = []
        params = list(map(lambda param: self.param_auto_checker(param), params))
        if not engine:
            engine = self.new_engine(self.previous_engine)
    
        contract_hash = self.contract_hash_auto_checker(contract_hash)
        # engine.load_script(vm.Script(contract.script))
        sb = vm.ScriptBuilder()
        if params:
            sb.emit_dynamic_call_with_args(contract_hash, method, params)
        else:
            sb.emit_dynamic_call(contract_hash, method)
        engine.load_script(vm.Script(sb.to_array()))
    
        if signers and signers != self.NO_SIGNER:
            signers = list(map(lambda signer:
                               self.signer_auto_checker(signer, scope),
                               signers))
            engine.script_container.signers = signers
        elif self.signers:  # use signers stored in self when no external signer specified
            engine.script_container.signers = self.signers
    
        engine.execute()
        engine.snapshot.commit()
        self.previous_engine = engine
        return engine

    def analyze_results(self, engine: ApplicationEngine = None, result_interpreted_as_hex=False,
                        result_interpreted_as_iterator=False, further_interpreter:Callable = None) -> Tuple[vm.VMState, Any]:
        if not engine:
            engine = self.previous_engine
        if not engine.result_stack:
            return engine.state, engine.result_stack
        result = engine.result_stack.peek()
        if result and result_interpreted_as_hex:
            processed_result = bytes.fromhex(str(result))
        elif result and result_interpreted_as_iterator:
            processed_result = dict()
            iterator = list(result.get_object().it)
            for k,v in iterator:
                processed_result[k.key] = v.value
        else:
            processed_result = str(result)
        if further_interpreter:
            processed_result = further_interpreter(processed_result)
        self.previous_processed_result = processed_result
        return engine.state, processed_result
    
    def print_results(self, engine: ApplicationEngine = None, result_interpreted_as_hex=False,
                      result_interpreted_as_iterator=False, further_interpreter:Callable = None) -> None:
        state, result = self.analyze_results(engine,
                        result_interpreted_as_hex, result_interpreted_as_iterator, further_interpreter)
        print(state, result)
    
    def reset_environment(self):
        """
        reset the blockchain environment, and re-deploy all the contracts that have been deployed.
        """
        self.previous_engine = self.new_engine()
        for contract in self.deployed_contracts:
            self.previous_engine.snapshot.contracts.put(contract)
            
    def set_NEP17_token_balance(self, token_contract: Union[contracts.ContractState, NativeContract], account:Union[UInt160, str],
                                amount: Union[int, float] = 2000000000, bytes_needed: int = None):
        """
        This is achieved by directly changing the storage of the NEP17 contract
        :param token_contract: contract managing the token
        :param account: ScriptHash of wallet which will receive the token
        :param amount: care for the decimals!
        :param bytes_needed: how many bytes are used in the contract to represent the number of tokens
        :return:
        """
        amount = int(amount)
        assert 0 <= amount <= 2147483647  # 0x7fffffff  # overflowing values result in minus balance
        engine = self.new_engine(self.previous_engine)
        account = self.param_auto_checker(account)
        if token_contract == neo:
            bytes_needed = 9
        contracts.interop.storage_put(engine, StorageContext(token_contract.id, False),
                                      self.Prefix_Account_bytes + account,
                                      self.Number_Prefix + EngineResultInterpreter.int_to_bytes(amount, bytes_needed=bytes_needed))
        engine.snapshot.commit()
        self.previous_engine = engine
        
    def get_rToken_balance(self, rToken_address: Union[Hash160Str, UInt160, str], owner: Union[Hash160Str, UInt160, str]):
        type_rToken_address = type(rToken_address)
        if type_rToken_address is Hash160Str or type_rToken_address is str:
            rToken_address = types.UInt160.from_string(str(rToken_address)[2:])
        self.invoke_method_of_arbitrary_contract(rToken_address, "balanceOf", [owner])
        
    def __repr__(self):
        if self.previous_processed_result:
            return f'class TestEngine: {self.state} {self.previous_processed_result}'
        else:
            return f'class TestEngine: {self.state}; no previous_processed_result'
