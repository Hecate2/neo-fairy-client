from typing import List, Tuple, Union, Dict, Any, Callable
from enum import Enum
import base64
import json
import os
import random
import traceback
import requests
import urllib3

from neo_fairy_client.utils import Hash160Str, Hash256Str, PublicKeyStr, Signer
from neo_fairy_client.utils import Interpreter, to_list
from neo_fairy_client.utils import ContractManagementAddress, CryptoLibAddress, GasAddress, LedgerAddress, NeoAddress, OracleAddress, PolicyAddress, RoleManagementAddress, StdLibAddress
from neo_fairy_client.utils import NamedCurveHash, defaultFairyWalletScriptHash

from neo_fairy_client.utils import UInt160, UInt256
from neo_fairy_client.utils import VMState, WitnessScope
from neo_fairy_client.utils.oracle import OracleRequest, OracleResponseCode

RequestExceptions = (
    requests.RequestException,
    requests.ConnectionError,
    requests.HTTPError,
    requests.Timeout,
)
default_request_timeout = None  # 20
default_requests_session = requests.Session()


class RpcBreakpoint:
    def __init__(self, state: Union[str, VMState], break_reason: str, scripthash: Union[str, int, Hash160Str], contract_name: str,
                 instruction_pointer: int, source_filename: str = None, source_line_num: int = None, source_content=None,
                 exception: str = None, result_stack: Any = None):
        if type(state) is VMState:
            self.state = state
        else:
            self.state: VMState = {'BREAK': VMState.BREAK, 'FAULT': VMState.FAULT, 'HALT': VMState.HALT, 'NONE': VMState.NONE}[state.upper()]
        self.break_reason = break_reason
        scripthash = Hash160Str.from_str_or_int(scripthash)
        self.scripthash = scripthash
        self.contract_name = contract_name
        self.instruction_pointer = instruction_pointer
        self.source_filename = source_filename
        self.source_line_num = source_line_num
        self.source_content = source_content
        self.exception = exception
        self.result_stack = result_stack
        
    @classmethod
    def from_raw_result(cls, result: Dict):
        result = result['result']
        return cls(result['state'], result['breakreason'], result['scripthash'], result['contractname'],
                   result['instructionpointer'], source_filename=result['sourcefilename'], source_line_num=result['sourcelinenum'], source_content=result['sourcecontent'])
    
    def __repr__(self):
        if self.state == VMState.HALT:
            return f'''{self.state} {self.result_stack}'''
        if self.source_filename and self.source_line_num:
            return f'''{self.state} {self.break_reason} {self.source_filename} line {self.source_line_num} instructionPointer {self.instruction_pointer}: {self.source_content}'''
        else:
            return f'''{self.state} {self.break_reason} {self.contract_name} instructionPointer {self.instruction_pointer};'''


class FairyClient:
    def __init__(self, target_url: str = 'http://localhost:16868',
                 wallet_address_or_scripthash: Union[str, int, Hash160Str] = None,
                 contract_scripthash: Union[str, int, Hash160Str] = None, signers: Union[Signer, List[Signer], None] = None,
                 fairy_session: str = None, function_default_relay=True, script_default_relay=False,
                 confirm_relay_to_blockchain=False,
                 auto_reset_fairy_session=True,
                 with_print=True, verbose_return=False, verify_SSL: bool = True,
                 requests_session: requests.Session = default_requests_session,
                 requests_timeout: Union[int, None] = default_request_timeout,
                 auto_set_neo_balance=100_0000_0000, auto_set_gas_balance=100_0000_0000,
                 auto_preparation=True,
                 hook_function_after_rpc_call: Callable = None,
                 default_fairy_wallet_scripthash: Union[str, int, Hash160Str] = defaultFairyWalletScriptHash):
        """
        Fairy RPC client to interact with both normal Neo3 and Fairy RPC backend.
        Fairy RPC backend helps you test and debug transactions with sessions, which contain snapshots.
        Use fairy_session strings to name your snapshots.
        :param target_url: url to the rpc server affiliated to neo-cli
        :param wallet_address_or_scripthash: address of your wallet (starting with 'N'); "NVbGwMfRQVudTjWAUJwj4K68yyfXjmgbPp"
        :param signers: by default, which account(s) will sign the transactions with which scope
            https://docs.neo.org/docs/en-us/basic/concept/transaction.html#signature-scope
        :param fairy_session: Any string designated by you to name your session which contains snapshot.
            If None, will use normal RPC without session string. No snapshot will be used or recorded
        :param function_default_relay: if True, will write your transaction to chain or fairy snapshot
        :param script_default_relay: if True, will write your transaction to chain or fairy snapshot
        :param confirm_relay_to_blockchain: if True, will ask for your confirmation before
            writing any transaction to the actual blockchain. Recommended for doing anything critical on the mainnet.
        :param with_print: print results for each RPC call
        :param verbose_return: return (parsed_result, raw_result, post_data) if True. return parsed result if False.
            This is to avoid reading previous_result for concurrency safety.
            For concurrency, set verbose_return=True
        :param requests_session: requests.Session
        :param requests_timeout: raise Exceptions if request not completed in that many seconds. None for no limit
        :param auto_preparation: prepares environments for common usage at a small cost of time
        :param hook_function_after_rpc_call: a function with no input argument, executed after each successful RPC call
        """
        self.target_url: str = target_url
        self.contract_scripthash: Union[Hash160Str, None] = Hash160Str.from_str_or_int(contract_scripthash)
        self.requests_session: requests.Session = requests_session
        if wallet_address_or_scripthash:
            wallet_scripthash: Hash160Str = Hash160Str.from_str_or_int(wallet_address_or_scripthash)
            self.wallet_address = wallet_scripthash.to_address()
            self.wallet_scripthash = wallet_scripthash
            self.signers: List[Signer] = to_list(signers) or [Signer(self.wallet_scripthash)]
        else:
            self.wallet_address = None
            self.wallet_scripthash = None
            self.signers: List[Signer] = signers or []
            print('WARNING: No wallet address specified when building the fairy client!')
        self.previous_post_data = None
        self.with_print: bool = with_print
        self.previous_raw_result: Union[dict, None] = None
        self.previous_result: Any = None
        self.previous_txBase64Str: Union[str, None] = None
        self.previous_gas_consumed: Union[int, None] = None
        self.previous_network_fee: Union[int, None] = None
        self.verbose_return: bool = verbose_return
        self.function_default_relay: bool = function_default_relay
        self.script_default_relay: bool = script_default_relay
        self.confirm_relay_to_blockchain: bool = confirm_relay_to_blockchain
        self.fairy_session: Union[str, None] = fairy_session
        self.verify_SSL: bool = verify_SSL
        self.requests_timeout: Union[int, None] = requests_timeout
        self.hook_function_after_rpc_call = hook_function_after_rpc_call
        self.default_fairy_wallet_scripthash = Hash160Str.from_str_or_int(default_fairy_wallet_scripthash)
        if verify_SSL is False:
            print('WARNING: Will ignore SSL certificate errors!')
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        if fairy_session and auto_preparation:
            try:
                if auto_reset_fairy_session:
                    self.new_snapshots_from_current_system(fairy_session)
                    self.set_gas_balance(1000_0000_0000, fairy_session=fairy_session, account=default_fairy_wallet_scripthash)
                if auto_set_neo_balance and self.wallet_scripthash:
                    self.set_neo_balance(auto_set_neo_balance)
                if auto_set_gas_balance and self.wallet_scripthash:
                    self.set_gas_balance(auto_set_gas_balance)
            except:
                traceback.print_exc()
                print(f"WARNING: Failed at some fairy operations at {target_url}!")

    def set_wallet_address_and_signers(self, wallet_address: Union[str, int, Hash160Str], signers: Union[Signer, List[Signer]] = None):
        """
        :param wallet_address: address of your wallet (starting with 'N'); "NVbGwMfRQVudTjWAUJwj4K68yyfXjmgbPp", or scripthash
        :param signers: Signer(wallet_scripthash or wallet_address). By Signer you can assign WitnessScope
        """
        if wallet_address.startswith('N'):
            self.wallet_address: str = wallet_address
            wallet_scripthash = Hash160Str.from_address(wallet_address)
            self.wallet_scripthash: Hash160Str = wallet_scripthash
        else:  # is scripthash
            wallet_scripthash = Hash160Str.from_str_or_int(wallet_address)
            self.wallet_scripthash = wallet_scripthash
            self.wallet_address = Hash160Str.to_address(wallet_scripthash)
        self.signers: List[Signer] = to_list(signers) or [Signer(wallet_scripthash)]

    @staticmethod
    def request_body_builder(method, parameters: List):
        return json.dumps({
            "jsonrpc": "2.0",
            "method": method,
            "params": parameters,
            "id": 1,
        }, separators=(',', ':'))
    
    @staticmethod
    def bytes_to_Hash160Str(bytestring: Union[bytes, bytearray]):
        return Hash160Str.from_UInt160(UInt160(bytestring))
    
    @staticmethod
    def base64_struct_to_bytestrs(base64_struct: dict) -> List[bytes]:
        processed_struct = []
        if type(base64_struct) is dict and 'type' in base64_struct and base64_struct['type'] == 'Struct':
            values = base64_struct['value']
            for value in values:
                if value['type'] == 'ByteString':
                    processed_struct.append(base64.b64decode(value['value']))
        return processed_struct
    
    def meta_rpc_method_with_raw_result(self, method: str, parameters: List) -> Any:
        post_data = self.request_body_builder(method, parameters)
        self.previous_post_data = post_data
        result = json.loads(self.requests_session.post(self.target_url, post_data, timeout=self.requests_timeout).text)
        if 'error' in result:
            raise ValueError(result['error'])
        self.previous_raw_result = result
        self.previous_result = None
        if self.hook_function_after_rpc_call:
            self.hook_function_after_rpc_call()
        return result

    def meta_rpc_method(self, method: str, parameters: List, relay: bool = None, do_not_raise_on_result=False) -> Any:
        post_data = self.request_body_builder(method, parameters)
        self.previous_post_data = post_data
        result = json.loads(self.requests_session.post(self.target_url, post_data, timeout=self.requests_timeout, verify=self.verify_SSL).text)
        self.previous_raw_result = result
        if 'error' in result:
            raise ValueError(f"""{result['error']['message']}\r\n{result['error']['data']}""" if 'data' in result['error'] else result['error'])
        if type(result['result']) is dict:
            result_result: dict = result['result']
            if gas_consumed := result_result.get('gasconsumed'):
                self.previous_gas_consumed = int(gas_consumed)
            if gas_consumed := result_result.get('networkfee'):
                self.previous_network_fee = int(gas_consumed)
            if 'exception' in result_result and result_result['exception'] is not None:
                if do_not_raise_on_result:
                    return result_result['exception']
                else:
                    print(post_data)
                    print(result)
                    if 'traceback' in result_result and result_result['traceback']:
                        raise ValueError(result_result['traceback'])
                    raise ValueError(result_result['exception'])
            if relay or (relay is None and self.function_default_relay):
                if method in {'invokefunction', 'invokescript'} and 'tx' not in result_result:
                    raise ValueError('No `tx` in response. '
                                     'Did you call `client.openwallet()` before `invokefunction`?'
                                     'Alternatively, set FairyClient(function_default_relay=False)')
                if 'tx' in result_result:
                    tx = result_result['tx']
                    self.previous_txBase64Str = tx
                    if self.confirm_relay_to_blockchain is False \
                        or input(f"Write transaction {tx} to the actual blockchain instead of Fairy? "
                                 f"Y/[n]: ") == "Y":
                        self.sendrawtransaction(tx)
                # else:
                #     self.previous_txBase64Str = None
        self.previous_result = self.parse_stack_from_raw_result(result)
        if self.hook_function_after_rpc_call:
            self.hook_function_after_rpc_call()
        if self.verbose_return:
            return self.previous_result, result, post_data
        return self.previous_result
    
    def print_previous_result(self):
        print(self.previous_result)
    
    def sendrawtransaction(self, transaction: str):
        """
        :param transaction: result['tx']. e.g. "ALmNfAb4lqIAAA...="
        """
        return self.meta_rpc_method("sendrawtransaction", [transaction], relay=False)
    
    def getrawtransaction(self, transaction_hash: Union[str, int, Hash256Str], verbose: bool = False):
        return self.meta_rpc_method("getrawtransaction", [Hash256Str.from_str_or_int(transaction_hash).to_str(), verbose], relay=False)
    
    def calculatenetworkfee(self, txBase64Str):
        return self.meta_rpc_method("calculatenetworkfee", [txBase64Str], relay=False)
    
    @property
    def totalfee(self):
        return self.previous_network_fee + self.previous_gas_consumed

    @property
    def previous_total_fee(self):
        return self.totalfee

    @property
    def previous_system_fee(self):
        return self.previous_gas_consumed
    
    def openwallet(self, path: str, password: str) -> dict:
        """
        WARNING: usually you should use this method along with __init__.
        Use another TestClient object to open another wallet
        """
        if self.verbose_return:
            open_wallet_result, _, _ = self.meta_rpc_method("openwallet", [path, password])
        else:
            open_wallet_result = self.meta_rpc_method("openwallet", [path, password])
        if not open_wallet_result:
            raise ValueError(f'Failed to open wallet {path} with given password.')
        return open_wallet_result

    def closewallet(self) -> dict:
        if self.verbose_return:
            close_wallet_result, _, _ = self.meta_rpc_method("closewallet", [])
        else:
            close_wallet_result = self.meta_rpc_method("closewallet", [])
        if not close_wallet_result:
            raise ValueError(f'Failed to close wallet.')
        return close_wallet_result

    def traverse_iterator(self, sid: str, iid: str, count=100) -> dict:
        post_data = self.request_body_builder('traverseiterator', [sid, iid, count])
        self.previous_post_data = post_data
        result = json.loads(self.requests_session.post(self.target_url, post_data, timeout=self.requests_timeout, verify=self.verify_SSL).text)['result']
        result_dict = dict()
        for kv in result:
            kv = kv['value']
            result_dict[self.parse_single_item(kv[0])] = self.parse_single_item(kv[1])
        return result_dict

    def parse_single_item(self, item: Union[Dict, List]):
        if 'iterator' in item:
            item = item['iterator']
            if item:
                if type(item[0]['value']) is not list:
                    return [self.parse_single_item(i) for i in item]
                else:
                    return {self.parse_single_item(i['value'][0]): self.parse_single_item(i['value'][1]) for i in item}
            else:
                assert item == []
                return item
        _type = item['type']
        if _type == 'Any' and 'value' not in item:
            return None
        elif _type == 'InteropInterface' and 'id' in item:
            session: str = self.previous_raw_result['result']['session']
            iterator_id: str = item['id']
            return self.traverse_iterator(session, iterator_id)
        else:
            value = item['value']
        if _type == 'Integer':
            return int(value)
        elif _type == 'Boolean':
            return value
        elif _type == 'ByteString' or _type == 'Buffer':
            byte_value = base64.b64decode(value)
            try:
                return byte_value.decode()
            except UnicodeDecodeError:
                try:
                    len_bytes = len(byte_value)
                    if len_bytes == 20:
                        return Hash160Str.from_UInt160(UInt160(byte_value))
                    if len_bytes == 32:
                        return Hash256Str.from_UInt256(UInt256(byte_value))
                except Exception:
                    pass
                # may be an N3 address starting with 'N'
                # TODO: decode to N3 address
                return byte_value
        elif _type == 'Array':
            return [self.parse_single_item(i) for i in value]
        elif _type == 'Struct':
            return tuple([self.parse_single_item(i) for i in value])
        elif _type == 'Map':
            return {self.parse_single_item(i['key']): self.parse_single_item(i['value']) for i in value}
        elif _type == 'Pointer':
            return int(value)
        else:
            raise ValueError(f'Unknown type {_type}')

    def parse_stack_from_raw_result(self, raw_result: dict):
        result: Dict = raw_result['result']
        if type(result) is not dict or 'stack' not in result:
            return result
        if not result['stack']:
            return result['stack']
        stack: List = result['stack']
        if len(stack) > 1:  # typically happens when we invoke a script calling a series of methods
            return [self.parse_single_item(item) for item in stack]
        else:  # if the stack has only 1 item, we simply return the item without a wrapping list
            result: List = stack[0]
            return self.parse_single_item(result)
    
    @classmethod
    def parse_param(cls, param: Union[str, int, dict, Hash160Str, UInt160, UInt256, bytes, bytearray]) -> Dict[str, str]:
        type_param = type(param)
        if type_param is UInt160:
            return {
                'type': 'Hash160',
                'value': str(Hash160Str.from_UInt160(param)),
            }
        elif type_param is Hash160Str:
            return {
                'type': 'Hash160',
                'value': str(param),
            }
        elif type_param is UInt256:
            return {
                'type': 'Hash256',
                'value': str(Hash256Str.from_UInt256(param)),
            }
        elif type_param is Hash256Str:
            return {
                'type': 'Hash256',
                'value': str(param),
            }
        elif type_param is PublicKeyStr:
            return {
                'type': 'PublicKey',
                'value': str(param),
            }
        elif type_param is bool:
            return {
                'type': 'Boolean',
                'value': param,
            }
        elif type_param is int:
            return {
                'type': 'Integer',
                'value': str(param),
            }
        elif type_param is str:
            return {
                'type': 'String',
                'value': param,
            }
        elif type_param is bytes or type_param is bytearray:
            # not the best way to judge, but maybe no better method
            try:
                return {
                    'type': 'String',
                    'value': param.decode(),
                }
            except UnicodeDecodeError:
                return {
                    'type': 'ByteArray',
                    'value': base64.b64encode(param).decode()
                }
        elif type_param is list:
            return {
                'type': 'Array',
                'value': [cls.parse_param(param_) for param_ in param]
            }
        elif type_param is dict:
            return {
                'type': 'Map',
                'value': [{'key': cls.parse_param(k), 'value': cls.parse_param(v)} for k, v in param.items()]
            }
        elif param is None:
            return {
                'type': 'Any',
            }
        elif isinstance(param, Enum):
            return cls.parse_param(param.value)
        raise ValueError(f'Unable to handle param {param} with type {type_param}')
    
    def invokefunction_of_any_contract(self, scripthash: Union[str, int, Hash160Str], operation: str,
                                       params: List[Union[List, str, int, dict, Hash160Str, UInt160, bytes, bytearray]] = None,
                                       signers: Union[Signer, List[Signer]] = None, relay: bool = None, do_not_raise_on_result=False,
                                       with_print=True, fairy_session: str = None) -> Any:
        scripthash = Hash160Str.from_str_or_int(scripthash)
        fairy_session = fairy_session or self.fairy_session
        params = params or []
        signers = to_list(signers or self.signers)
        if self.with_print and with_print:
            if fairy_session:
                print(f'{fairy_session}::{operation}{params} relay={relay} {signers}')
            else:
                print(f'{operation}{params} relay={relay} {signers}')
        
        parameters = [
            str(scripthash),
            operation,
            list(map(lambda param: self.parse_param(param), params)),
            list(map(lambda signer: signer.to_dict(), signers)),
        ]
        if fairy_session:
            result = self.meta_rpc_method(
                'invokefunctionwithsession', [fairy_session, relay or (relay is None and self.function_default_relay)] + parameters, relay=False,
                do_not_raise_on_result=do_not_raise_on_result)
        else:
            result = self.meta_rpc_method('invokefunction', parameters, relay=relay,
                                          do_not_raise_on_result=do_not_raise_on_result)
        return result
    
    def invokefunction(self, operation: str, params: List[Union[List, str, int, Hash160Str, UInt160, bytes, bytearray]] = None,
                       signers: Union[Signer, List[Signer]] = None, relay: bool = None, do_not_raise_on_result=False, with_print=True,
                       fairy_session: str = None) -> Any:
        if self.contract_scripthash is None or self.contract_scripthash == Hash160Str.zero():
            raise ValueError(f'Please set client.contract_scripthash before invoking function. Got {self.contract_scripthash}')
        return self.invokefunction_of_any_contract(self.contract_scripthash, operation, params,
                                                   signers=signers, relay=relay or (relay is None and self.function_default_relay),
                                                   do_not_raise_on_result=do_not_raise_on_result,
                                                   with_print=with_print, fairy_session=fairy_session)
    
    def invokemany(self, call_arguments: List[List[Union[Hash160Str, str, List[Any]]]],
                   signers: Union[Signer, List[Signer]] = None, relay: bool = None, do_not_raise_on_result=False, with_print=True,
                   fairy_session: str = None):
        """
        :param call_arguments: [ [contract_scripthash: Hash160Str, operation: str, args[] ], [operation, args[] ], [operation] ]
            Use Hash160Str and do not input str for contract_scripthash, because it can be recognized as operation str.
        """
        fairy_session = fairy_session or self.fairy_session
        assert fairy_session  # only supports sessioned calls for now
        signers = to_list(signers or self.signers)
        if self.with_print and with_print:
            print(f'{fairy_session}::{call_arguments} relay={relay} {signers}')
    
        parsed_call_arguments = [  # [ [contract_scripthash: Hash160Str, operation: str, args[] ] ]
            [# [ contract_scripthash: Hash160Str, operation: str, args[] ] or [ operation: str, args[] ]
                str(call[0]) if type(call[0]) is Hash160Str else str(self.contract_scripthash),
                call[1] if type(call[0]) is Hash160Str else call[0],
                list(map(lambda param: self.parse_param(param), call[-1]) if len(call) >= 2 else [])
            ]
            for call in call_arguments
        ]
        return self.meta_rpc_method(
            'invokemanywithsession', [fairy_session, relay or (relay is None and self.function_default_relay), parsed_call_arguments, list(map(lambda signer: signer.to_dict(), signers))], relay=False,
            do_not_raise_on_result=do_not_raise_on_result)

    def invokescript(self, script_base64_encoded: Union[str, bytes], signers: Union[Signer, List[Signer]] = None, relay: bool = None,
                     fairy_session: str = None) -> Any:
        if type(script_base64_encoded) is bytes:
            script_base64_encoded: str = script_base64_encoded.decode()
        signers = to_list(signers or self.signers)
        fairy_session = fairy_session or self.fairy_session
        if fairy_session:
            relay = relay or (relay is None and self.script_default_relay)
            result = self.meta_rpc_method(
                'invokescriptwithsession',
                [fairy_session, relay, script_base64_encoded, list(map(lambda signer: signer.to_dict(), signers))],
                relay=False)
        else:
            result = self.meta_rpc_method(
                'invokescript',
                [script_base64_encoded, list(map(lambda signer: signer.to_dict(), signers))],
                relay=relay)
        return result
    
    def oracle_finish(self, oracle_result: Union[str, bytes], oracle_request_id: Union[OracleRequest, Dict, List, int, None] = None,
                      oracle_response_code: Union[OracleResponseCode, int] = OracleResponseCode.Success,
                      debug = False, relay: bool = None, fairy_session: str = None) -> Any:
        """
        :param oracle_result: Do not have it b64encode-ed, but have it filtered with json path.
        :param oracle_request_id:
        :param oracle_response_code:
        :param relay:
        :param fairy_session:
        :return:
        """
        fairy_session = fairy_session or self.fairy_session
        if type(oracle_result) is str:
            oracle_result: bytes = oracle_result.encode()
        oracle_result: str = base64.b64encode(oracle_result).decode()
        if oracle_request_id is None:
            oracle_request_id = OracleRequest(self.previous_raw_result['result']['oraclerequests'][0]).request_id
        if type(oracle_request_id) is list or type(oracle_request_id) is dict:
            oracle_request_id: OracleRequest = OracleRequest(oracle_request_id)
        if type(oracle_request_id) is OracleRequest:
            oracle_request_id: int = oracle_request_id.request_id
        if type(oracle_response_code) is OracleResponseCode:
            oracle_response_code.value: int
            oracle_response_code: int = oracle_response_code.value
        result = self.meta_rpc_method_with_raw_result(
            "oraclefinish", [fairy_session, relay or (relay is None and self.function_default_relay),
            oracle_request_id, oracle_response_code, oracle_result, debug])
        return result
    
    def oracle_json_path(self, json_input: Union[str, Dict], json_path: str) -> bytes:
        if type(json_input) is dict:
            json_input: str = json.dumps(json_input, separators=(',', ':'))
        result: Dict[str, str] = self.meta_rpc_method_with_raw_result(
            "oraclejsonpath", [json_input, json_path])
        return base64.b64decode(result['result'])
    
    def replay_transaction(self, tx_hash: Union[str, int, Hash256Str], signers: Union[Signer, List[Signer]] = None, relay: bool = None,
                           fairy_session: str = None, debug = False) -> Any:
        """
        Get a transaction already existing on chain, and re-execute its script
        :param signers: if None, use signers of the specified transaction
        """
        tx_hash: Hash256Str = Hash256Str.from_str_or_int(tx_hash)
        tx = self.await_confirmed_transaction(tx_hash, True)
        signers = signers or [Signer.from_dict(s) for s in tx['signers']]
        if not debug:
            return self.invokescript(tx['script'], signers=signers, relay=relay, fairy_session=fairy_session)
        return self.debug_script_with_session(tx['script'], signers=signers, relay=relay, fairy_session=fairy_session)
    
    def get_block_count(self) -> int:
        return self.meta_rpc_method("getblockcount", [])
    
    def sendfrom(self, asset_id: Union[str, int, Hash160Str], from_address: Union[str, int, Hash160Str], to_address: str, value: int,
                 signers: List[Signer] = None):
        """

        :param asset_id: NEO: '0xef4073a0f2b305a38ec4050e4d3d28bc40ea63f5';
            GAS: '0xd2a4cff31913016155e38e474a2c06d08be276cf'
        :param from_address: "NgaiKFjurmNmiRzDRQGs44yzByXuSkdGPF"
        :param to_address: "NikhQp1aAD1YFCiwknhM5LQQebj4464bCJ"
        :param value: 100000000, including decimals
        :param signers:
        :return:
        """
        signers = to_list(signers or self.signers)
        return self.meta_rpc_method('sendfrom', [
            Hash160Str.from_str_or_int(asset_id).to_str(),
            Hash160Str.from_str_or_int(from_address).to_str(), Hash160Str.from_str_or_int(to_address).to_str(), value,
            signers
        ])
    
    def sendtoaddress(self, asset_id: Union[str, int, Hash160Str], address, value: int):
        return self.meta_rpc_method('sendtoaddress', [
            Hash160Str.from_str_or_int(asset_id).to_str(), address, value,
        ])
    
    def send_neo_to_address(self, to_address: Union[str, int, Hash160Str], value: int):
        return self.sendtoaddress(NeoAddress, Hash160Str.from_str_or_int(to_address), value)
    
    def send_gas_to_address(self, to_address: Union[str, int, Hash160Str], value: int):
        return self.sendtoaddress(GasAddress, Hash160Str.from_str_or_int(to_address), value)
    
    def getwalletbalance(self, asset_id: Union[str, int, Hash160Str]) -> int:
        return int(self.meta_rpc_method('getwalletbalance', [Hash160Str.from_str_or_int(asset_id).to_str()])['balance'])
    
    def get_neo_balance(self, owner: Union[str, int, Hash160Str] = None, with_print=False) -> int:
        return self.invokefunction_of_any_contract(NeoAddress, 'balanceOf', params=[Hash160Str.from_str_or_int(owner) or self.wallet_scripthash], relay=False, with_print=with_print)
        # return self.getwalletbalance(Hash160Str.from_UInt160(NeoToken().hash))

    def get_gas_balance(self, owner: Union[str, int, Hash160Str] = None, with_print=False) -> int:
        return self.invokefunction_of_any_contract(GasAddress, 'balanceOf', params=[Hash160Str.from_str_or_int(owner) or self.wallet_scripthash], relay=False, with_print=with_print)
        # return self.getwalletbalance(Hash160Str.from_UInt160(GasToken().hash))
    
    def get_nep17token_balance(self, token_address: Union[str, int, Hash160Str], owner: Union[str, int, Hash160Str] = None, with_print=False):
        return self.invokefunction_of_any_contract(Hash160Str.from_str_or_int(token_address), "balanceOf", params=[Hash160Str.from_str_or_int(owner) or self.wallet_scripthash], relay=False, with_print=with_print)

    def get_nep11token_balance(self, token_address: Union[str, int, Hash160Str], tokenId: Union[bytes, str, int], owner: Union[str, int, Hash160Str] = None, with_print=False):
        return self.invokefunction_of_any_contract(Hash160Str.from_str_or_int(token_address), "balanceOf", params=[Hash160Str.from_str_or_int(owner) or self.wallet_scripthash, tokenId], relay=False, with_print=with_print)

    b"""
    Fairy features below! Mount your neo-cli RpcServer with
    https://github.com/Hecate2/neo-fairy-test/
    before using the following methods!
    """

    def hello_fairy(self) -> dict:
        return self.meta_rpc_method("hellofairy", [])

    def open_default_fairy_wallet(self, path: str, password: str) -> dict:
        if self.verbose_return:
            open_wallet_result, _, _ = self.meta_rpc_method("opendefaultfairywallet", [path, password])
        else:
            open_wallet_result = self.meta_rpc_method("opendefaultfairywallet", [path, password])
        if not open_wallet_result:
            raise ValueError(f'Failed to open default wallet {path} with given password.')
        return open_wallet_result

    def reset_default_fairy_wallet(self) -> dict:
        if self.verbose_return:
            close_wallet_result, _, _ = self.meta_rpc_method("resetdefaultfairywallet", [])
        else:
            close_wallet_result = self.meta_rpc_method("resetdefaultfairywallet", [])
        if not close_wallet_result:
            raise ValueError(f'Failed to reset default wallet.')
        return close_wallet_result

    def set_session_fairy_wallet_with_NEP2(self, nep2: Union[str, List[str]], password: Union[str, List[str]], fairy_session: str = None) -> dict:
        wallets = []
        for n, p in zip(to_list(nep2), to_list(password)):
            wallets += [n, p]
        open_wallet_result = self.meta_rpc_method("setsessionfairywalletwithnep2", [fairy_session or self.fairy_session] + wallets)
        if not open_wallet_result:
            raise ValueError(f'Failed to open NEP2 wallet {nep2} with given password.')
        return open_wallet_result

    def set_session_fairy_wallet_with_WIF(self, wif: Union[str, List[str]], fairy_session: str = None) -> dict:
        open_wallet_result = self.meta_rpc_method("setsessionfairywalletwithwif", [fairy_session or self.fairy_session] + to_list(wif))
        if not open_wallet_result:
            raise ValueError(f'Failed to open WIF wallet {wif} with given password.')
        return open_wallet_result

    def force_verify_with_ecdsa(
            self, message_base64_encoded: Union[str, bytes],
            pubkey: Union[PublicKeyStr, str, bytes],
            signature_base64_encoded: Union[str, bytes],
            namedCurveHash: Union[NamedCurveHash, bytes, int] = NamedCurveHash.secp256r1SHA256) -> bool:
        if type(message_base64_encoded) is bytes:
            message_base64_encoded: str = base64.b64encode(message_base64_encoded).decode()
        if type(pubkey) is PublicKeyStr:
            pubkey: bytearray = pubkey.to_bytes()
        pubkey: str = base64.b64encode(pubkey).decode()
        if type(signature_base64_encoded) is bytes:
            signature_base64_encoded: str = base64.b64encode(signature_base64_encoded).decode()
        if type(namedCurveHash) is bytes:
            namedCurveHash: int = namedCurveHash[0]
        if type(namedCurveHash) is int:
            namedCurveHash: NamedCurveHash = NamedCurveHash(namedCurveHash)
        return self.meta_rpc_method("forceverifywithecdsa", [message_base64_encoded, pubkey, signature_base64_encoded, namedCurveHash.value], relay=False)['result']

    def force_sign_message(self, message_base64_encoded: Union[str, bytes], namedCurveHash: Union[NamedCurveHash, bytes, int] = NamedCurveHash.secp256r1SHA256, fairy_session: str = None) -> bytes:
        fairy_session = fairy_session or self.fairy_session
        if type(message_base64_encoded) is bytes:
            message_base64_encoded: str = base64.b64encode(message_base64_encoded).decode()
        if type(namedCurveHash) is bytes:
            namedCurveHash: int = namedCurveHash[0]
        if type(namedCurveHash) is int:
            namedCurveHash: NamedCurveHash = NamedCurveHash(namedCurveHash)
        return base64.b64decode(self.meta_rpc_method("forcesignmessage", [fairy_session, message_base64_encoded, namedCurveHash.value], relay=False)['signed'])

    def force_sign_transaction(self, script_base64_encoded: Union[str, bytes, None] = None, fairy_session: str = None,
                               signers: List[Signer] = None, system_fee: int = 1000_0000, network_fee: int = 0,
                               valid_until_block: Union[int, None] = 0, nonce: int = 0) -> Dict[str, Any]:
        """
        Build and sign a transaction with the fairy wallet of the fairy_session,
        even if the transaction cannot be run correctly
        :param script_base64_encoded:
        :param fairy_session:
        :param signers:
        :param system_fee:
        :param network_fee:
        :param valid_until_block:
        :param nonce: WARNING: never publish multiple signatures using the same nonce! This will leak your private key!
        :return:
        """
        fairy_session = fairy_session or self.fairy_session
        if type(script_base64_encoded) is bytes:
            script_base64_encoded: str = script_base64_encoded.decode()
        script_base64_encoded: str = script_base64_encoded or self.previous_raw_result['result']['script']
        signers = to_list(signers or self.signers)
        valid_until_block = self.get_block_count() + 5760 if valid_until_block is None else valid_until_block
        nonce = nonce or random.randint(0, 2**32 - 1)
        result = self.meta_rpc_method("forcesigntransaction", [fairy_session, script_base64_encoded, list(map(lambda signer: signer.to_dict(), signers)), system_fee, network_fee, valid_until_block, nonce], relay=False)
        if 'txHash' in result:
            result['txHash'] = Hash256Str(result['txHash'])
            self.previous_raw_result = result
        return result['tx']

    def get_time_milliseconds(self) -> int:
        """
        :return: blockchain timestamp in milliseconds
        """
        return self.meta_rpc_method('gettime', [])['time']

    def new_snapshots_from_current_system(self, fairy_sessions: Union[List[str], str] = None):
        fairy_sessions = fairy_sessions or self.fairy_session
        if fairy_sessions is None:
            raise ValueError('No Fairy session specified')
        if type(fairy_sessions) is str:
            return self.meta_rpc_method("newsnapshotsfromcurrentsystem", [fairy_sessions])
        return self.meta_rpc_method("newsnapshotsfromcurrentsystem", fairy_sessions)
    
    def delete_snapshots(self, fairy_sessions: Union[List[str], str]):
        return self.meta_rpc_method("deletesnapshots", to_list(fairy_sessions))
    
    def list_snapshots(self):
        return self.meta_rpc_method("listsnapshots", [])
    
    def rename_snapshot(self, old_name: str, new_name: str):
        return self.meta_rpc_method("renamesnapshot", [old_name, new_name])
    
    def copy_snapshot(self, old_name: str, new_name: str):
        return self.meta_rpc_method("copysnapshot", [old_name, new_name])
    
    def set_snapshot_timestamp(self, timestamp_ms: Union[int, None] = None, fairy_session: str = None) -> Dict[str, Union[int, None]]:
        """
        
        :param timestamp_ms: use None to reset to current block time
        :param fairy_session:
        :return:
        """
        fairy_session = fairy_session or self.fairy_session
        return self.meta_rpc_method("setsnapshottimestamp", [fairy_session, timestamp_ms])
    
    def get_snapshot_timestamp(self, fairy_sessions: Union[List[str], str, None] = None) -> Dict[str, Union[int, None]]:
        fairy_sessions = fairy_sessions or self.fairy_session
        if fairy_sessions is None:
            raise ValueError('No Fairy session specified')
        return self.meta_rpc_method("getsnapshottimestamp", to_list(fairy_sessions))

    def set_snapshot_random(self, designated_random: Union[int, None], fairy_session: str = None) -> Dict[str, Union[int, None]]:
        """
        @param designated_random: use None to delete the designated random and let Fairy choose any random number
        """
        fairy_session = fairy_session or self.fairy_session
        result = self.meta_rpc_method("setsnapshotrandom", [fairy_session, designated_random])
        for k in result:
            result[k] = None if result[k] is None else int(result[k])
        return result

    def get_snapshot_random(self, fairy_sessions: Union[List[str], str] = None) -> Dict[str, Union[int, None]]:
        fairy_sessions = fairy_sessions or self.fairy_session
        if type(fairy_sessions) is str:
            result = self.meta_rpc_method("getsnapshotrandom", [fairy_sessions])
        else:
            result = self.meta_rpc_method("getsnapshotrandom", fairy_sessions)
        for k, v in result.items():
            result[k] = None if not v else int(v)
        return result
    
    def set_snapshot_checkwitness(self, always_return_true: bool = True, fairy_session: str = None) -> Dict[str, bool]:
        fairy_session = fairy_session or self.fairy_session
        return self.meta_rpc_method("setsnapshotcheckwitness", [fairy_session, always_return_true])
    
    def get_snapshot_checkwitness(self, fairy_sessions: Union[List[str], str, None] = None) -> Dict[str, Union[bool, None]]:
        fairy_sessions = fairy_sessions or self.fairy_session
        if fairy_sessions is None:
            raise ValueError('No Fairy session specified')
        return self.meta_rpc_method("getsnapshotcheckwitness", to_list(fairy_sessions))
    
    def virtual_deploy(self, nef: bytes, manifest: str, data: Any = None, signers: Union[Signer, List[Signer]] = None, fairy_session: str = None) -> Hash160Str:
        """
        
        :param data: Contract parameter sent to _deploy method of contract
        :return:
        """
        fairy_session = fairy_session or self.fairy_session
        # check manifest
        manifest_dict = json.loads(manifest)
        if manifest_dict["permissions"] == [{'contract': '0xacce6fd80d44e1796aa0c2c625e9e4e0ce39efc0', 'methods': ['deserialize', 'serialize']}, {'contract': '0xfffdc93764dbaddd97c48f252a53ea4643faa3fd', 'methods': ['destroy', 'getContract', 'update']}]:
            print('!!!SERIOUS WARNING: Did you write [ContractPermission("*", "*")] in your contract?!!!')
        try:
            return Hash160Str(self.meta_rpc_method("virtualdeploy", [fairy_session, base64.b64encode(nef).decode(), manifest, self.parse_param(data), list(map(lambda signer: signer.to_dict(), to_list(signers or self.signers)))])[fairy_session])
        except Exception as e:
            print(f'If you have weird exceptions from this method, '
                  f'check if you have written any `null` to contract storage in `_deploy` method. '
                  f'Especially, consider marking your UInt160 properties of class '
                  f'as `static readonly UInt160` in your contract')
            raise e

    def get_many_blocks(self, indexes_or_hashes: List[Union[int, Hash256Str]]):
        '''
        
        :param indexes_or_hashes:
            2 uint indexes: get all blocks between the indexes
            other cases: get all blocks defined by each item in the list
        :return:
        '''
        return self.meta_rpc_method('getmanyblocks', indexes_or_hashes)

    def get_contract(self, scripthash: Union[str, int, Hash160Str] = None, fairy_session: str = None):
        scripthash = Hash160Str.from_str_or_int(scripthash) or self.contract_scripthash
        if not scripthash:
            raise ValueError("No contract scripthash specified!")
        fairy_session = fairy_session or self.fairy_session
        return self.meta_rpc_method("getcontract", [fairy_session, scripthash])

    def save_nef_manifest(self, scripthash: Union[str, int, Hash160Str] = None, nef_path_and_filename: str = None, fairy_session: str = None, auto_dumpnef=True) -> Tuple[bytes, str]:
        scripthash = Hash160Str.from_str_or_int(scripthash) or self.contract_scripthash
        contract_state = self.get_contract(scripthash, fairy_session=fairy_session)
        manifest = contract_state['manifest']
        nef_path_and_filename = nef_path_and_filename or f"{scripthash}.{manifest['name']}.nef"
        path, nef_filename = os.path.split(nef_path_and_filename)
        if nef_filename.endswith(".nef"):
            nef_filename = nef_filename[:-len(".nef")]
        if nef_filename.endswith(".manifest.json"):
            nef_filename = nef_filename[:-len(".manifest.json")]
        with open(os.path.join(path, f'{nef_filename}.manifest.json'), 'w') as f:
            f.write(json.dumps(manifest))
        nef_file: str = contract_state['nefFile']
        nef_file: bytes = base64.b64decode(nef_file)
        nef_path_and_filename = os.path.join(path, f'{nef_filename}.nef')
        with open(nef_path_and_filename, 'wb') as f:
            f.write(nef_file)
        if auto_dumpnef:
            print(f'dumpnef {nef_filename}', os.popen(f'dumpnef {nef_path_and_filename} > {nef_path_and_filename}.txt').read())
        return nef_file, manifest

    def list_contracts(self, verbose = False, fairy_session: str = None) -> Dict[str, Any]:
        fairy_session = fairy_session or self.fairy_session
        return self.meta_rpc_method("listcontracts", [fairy_session, verbose])

    def await_confirmed_transaction(self, tx_hash: Union[str, int, Hash256Str], verbose=True, wait_block_count = 2):
        return self.meta_rpc_method('awaitconfirmedtransaction', [Hash256Str.from_str_or_int(tx_hash), verbose, wait_block_count])

    @staticmethod
    def get_nef_and_manifest_from_path(nef_path_and_filename: str) -> Tuple[bytes, str]:
        path, nef_filename = os.path.split(nef_path_and_filename)  # '../NFTLoan/NFTLoan/bin/sc', 'NFTFlashLoan.nef'
        assert nef_filename.endswith('.nef')
        with open(nef_path_and_filename, 'rb') as f:
            nef = f.read()
        contract_path_and_filename = nef_path_and_filename[:-4]  # '../NFTLoan/NFTLoan/bin/sc/NFTFlashLoan'
        with open(contract_path_and_filename+".manifest.json", 'r', encoding='utf-8') as f:
            manifest = f.read()
        return nef, manifest

    def virutal_deploy_from_path(self, nef_path_and_filename: str, data: Any = None, fairy_session: str = None,
                                 auto_dumpnef=True, dumpnef_backup=True, auto_set_debug_info=True,
                                 auto_set_client_contract_scripthash=True) -> Hash160Str:
        """
        auto virtual deploy which also executes dumpnef (on your machine) and SetDebugInfo (with RPC)
        :param nef_path_and_filename: '../NFTLoan/NFTLoan/bin/sc/NFTFlashLoan.nef'
        :param data: Contract parameter sent to _deploy method of contract
        """
        fairy_session = fairy_session or self.fairy_session
        path, nef_filename = os.path.split(nef_path_and_filename)  # '../NFTLoan/NFTLoan/bin/sc', 'NFTFlashLoan.nef'
        assert nef_filename.endswith('.nef'), f"File name must end with .nef . Got {nef_filename}"
        with open(nef_path_and_filename, 'rb') as f:
            nef = f.read()
        contract_path_and_filename = nef_path_and_filename[:-4]  # '../NFTLoan/NFTLoan/bin/sc/NFTFlashLoan'
        with open(contract_path_and_filename+".manifest.json", 'r', encoding='utf-8') as f:
            manifest = f.read()
        contract_hash = self.virtual_deploy(nef, manifest, data=data, fairy_session=fairy_session)
        nefdbgnfo_path_and_filename = contract_path_and_filename + '.nefdbgnfo'
        dumpnef_path_and_filename = contract_path_and_filename + '.nef.txt'
        if os.path.exists(nefdbgnfo_path_and_filename):
            if auto_dumpnef and (not os.path.exists(dumpnef_path_and_filename) or os.path.getmtime(dumpnef_path_and_filename) < os.path.getmtime(nef_path_and_filename)):
                if dumpnef_backup and os.path.exists(dumpnef_path_and_filename) and not os.path.exists(contract_path_and_filename + '.bk.txt'):
                    # only backup the .nef.txt file when no backup exists
                    os.rename(dumpnef_path_and_filename, contract_path_and_filename + '.bk.txt')
                print(f'dumpnef {nef_filename}', os.popen(f'dumpnef {nef_path_and_filename} > {nef_path_and_filename}.txt').read())
            if auto_set_debug_info and os.path.exists(dumpnef_path_and_filename) \
                    and os.path.getmtime(dumpnef_path_and_filename) >= os.path.getmtime(nef_path_and_filename) \
                    and fairy_session:
                with open(nefdbgnfo_path_and_filename, 'rb') as f:
                    nefdbgnfo = f.read()
                with open(dumpnef_path_and_filename, 'r', encoding='utf-8') as f:
                    dumpnef = f.read()
                self.set_debug_info(nefdbgnfo, dumpnef, contract_hash)
        else:
            print('WARNING! No .nefdbgnfo found.'
                  'It is highly recommended to generate .nefdbgnfo for debugging.'
                  'If you are writing contracts in C#,'
                  'consider building your project with command `nccs your.csproj --debug`.')
        if auto_set_client_contract_scripthash:
            self.contract_scripthash = contract_hash
        return contract_hash

    @staticmethod
    def all_to_base64(key: Union[str, bytes, int]) -> str:
        if type(key) is str:
            encoded_key = key.encode(encoding='UTF-8',errors='strict')
            if not key.isascii():
                print(f'WARNING! non-ascii str input {key}. Your input will be utf8-encoded to bytes {encoded_key}')
            key = encoded_key
        if type(key) is int:
            key = Interpreter.int_to_bytes(key)
        if type(key) is bytes:
            key = base64.b64encode(key).decode()
        else:
            raise ValueError(f'Unexpected input type {type(key)} {key}')
        return key

    def get_storage_with_session(self, key: Union[str, bytes, int], debug: bool = False, fairy_session: str = None, contract_scripthash: Union[str, int, Hash160Str] = None) -> Dict[str, str]:
        """
        :param debug==True operates on the debug snapshot instead of the test snapshot
        """
        fairy_session = fairy_session or self.fairy_session
        contract_scripthash = Hash160Str.from_str_or_int(contract_scripthash) or self.contract_scripthash
        return self.meta_rpc_method("getstoragewithsession", [fairy_session, contract_scripthash, self.all_to_base64(key), debug])

    def find_storage_with_session(self, key: Union[str, bytes, int], debug: bool = False, fairy_session: str = None, contract_scripthash: Union[str, int, Hash160Str] = None) -> Dict[str, str]:
        """
        :param debug==True operates on the debug snapshot instead of the test snapshot
        """
        fairy_session = fairy_session or self.fairy_session
        contract_scripthash = Hash160Str.from_str_or_int(contract_scripthash) or self.contract_scripthash
        return self.meta_rpc_method("findstoragewithsession", [fairy_session, contract_scripthash, self.all_to_base64(key), debug])

    def put_storage_with_session(self, key: Union[str, bytes, int], value: Union[str, bytes, int], debug: bool = False, fairy_session: str = None, contract_scripthash: Union[str, int, Hash160Str] = None) -> Dict[str, str]:
        """
        :param value=="" deletes the key-value pair
        :param debug==True operates on the debug snapshot instead of the test snapshot
        """
        fairy_session = fairy_session or self.fairy_session
        contract_scripthash = Hash160Str.from_str_or_int(contract_scripthash) or self.contract_scripthash
        return self.meta_rpc_method("putstoragewithsession", [fairy_session, contract_scripthash, self.all_to_base64(key), self.all_to_base64(value), debug])

    def deserialize(self, data_base64encoded: Union[str, List[str]]) -> List[Any]:
        result = self.meta_rpc_method_with_raw_result('deserialize', to_list(data_base64encoded))['result']
        return [self.parse_single_item(item) for item in result]

    def set_neo_balance(self, balance: Union[int, float], fairy_session: str = None, account: Union[str, int, Hash160Str] = None):
        balance = int(balance)
        fairy_session = fairy_session or self.fairy_session
        account = Hash160Str.from_str_or_int(account) or self.wallet_scripthash
        if not account:
            raise ValueError('No account specified')
        return self.meta_rpc_method("setneobalance", [fairy_session, account, balance])

    def set_gas_balance(self, balance: Union[int, float], fairy_session: str = None, account: Union[str, int, Hash160Str] = None):
        balance = int(balance)
        fairy_session = fairy_session or self.fairy_session
        account = Hash160Str.from_str_or_int(account) or self.wallet_scripthash
        return self.meta_rpc_method("setgasbalance", [fairy_session, account, balance])

    def set_nep17_balance(self, contract: Union[str, int, Hash160Str], balance: int, fairy_session: str = None, account: Union[str, int, Hash160Str] = None, byte_prefix: int = 1):
        """
        We do not guarantee the success of this method.
        If the token contract is written with an unusual storage pattern,
        (e.g. fUSDT at 0xcd48b160c1bbc9d74997b803b9a7ad50a4bef020)
        you will need to modify the Fairy server to set the balance
        """
        if byte_prefix >= 256 or byte_prefix < 0:
            raise ValueError(f'Only 0<=byte_prefix<=255 accepted. Got {byte_prefix}')
        fairy_session = fairy_session or self.fairy_session
        account = Hash160Str.from_str_or_int(account) or self.wallet_scripthash
        return self.meta_rpc_method("setnep17balance", [fairy_session, Hash160Str.from_str_or_int(contract), account, balance, byte_prefix])

    def get_many_unclaimed_gas(self, accounts: Union[Hash160Str, List[Hash160Str]], fairy_session: str = None):
        accounts = to_list(accounts)
        fairy_session = fairy_session or self.fairy_session
        result = self.meta_rpc_method('getmanyunclaimedgas', [fairy_session, *accounts])
        return {account: int(amount) for account, amount in result.items()}

    b"""
    Fairy debugger features!
    """
    """debug info and file names"""
    def set_debug_info(self, nefdbgnfo: bytes, dumpnef_content: str, contract_scripthash: Union[str, int, Hash160Str] = None) -> Dict[Hash160Str, bool]:
        contract_scripthash = Hash160Str.from_str_or_int(contract_scripthash) or self.contract_scripthash
        return {Hash160Str(k): v for k, v in self.meta_rpc_method("setdebuginfo", [contract_scripthash, self.all_to_base64(nefdbgnfo), dumpnef_content]).items()}

    def list_debug_info(self) -> List[Hash160Str]:
        return [Hash160Str(i) for i in self.meta_rpc_method("listdebuginfo", [])]

    def list_filenames_of_contract(self, contract_scripthash: Union[str, int, Hash160Str] = None) -> List[Hash160Str]:
        contract_scripthash = Hash160Str.from_str_or_int(contract_scripthash) or self.contract_scripthash
        return self.meta_rpc_method("listfilenamesofcontract", [contract_scripthash])

    def delete_debug_info(self, contract_scripthashes: Union[List[Hash160Str], Hash160Str]) -> Dict[Hash160Str, bool]:
        if type(contract_scripthashes) is Hash160Str:
            result: Dict[str, bool] = self.meta_rpc_method("deletedebuginfo", [contract_scripthashes])
        else:
            result: Dict[str, bool] = self.meta_rpc_method("deletedebuginfo", contract_scripthashes)
        return {Hash160Str(k): v for k, v in result.items()}

    """breakpoints"""
    def set_assembly_breakpoints(self, instruction_pointers: Union[int, List[int]], contract_scripthash: Union[str, int, Hash160Str] = None):
        contract_scripthash = Hash160Str.from_str_or_int(contract_scripthash) or self.contract_scripthash
        if type(instruction_pointers) is int:
            return self.meta_rpc_method("setassemblybreakpoints", [contract_scripthash, instruction_pointers])
        else:
            return self.meta_rpc_method("setassemblybreakpoints", [contract_scripthash] + list(instruction_pointers))

    def list_assembly_breakpoints(self, contract_scripthash: Union[str, int, Hash160Str] = None):
        contract_scripthash = Hash160Str.from_str_or_int(contract_scripthash) or self.contract_scripthash
        return self.meta_rpc_method("listassemblybreakpoints", [contract_scripthash])

    def delete_assembly_breakpoints(self, instruction_pointers: Union[int, List[int]] = None, contract_scripthash: Union[str, int, Hash160Str] = None):
        contract_scripthash = Hash160Str.from_str_or_int(contract_scripthash) or self.contract_scripthash
        instruction_pointers = [] if instruction_pointers is None else instruction_pointers
        if type(instruction_pointers) is int:
            return self.meta_rpc_method("deleteassemblybreakpoints", [contract_scripthash, instruction_pointers])
        else:
            return self.meta_rpc_method("deleteassemblybreakpoints", [contract_scripthash] + list(instruction_pointers))

    def set_source_code_breakpoint(self, filename: str, line_num: int, contract_scripthash: Union[str, int, Hash160Str] = None):
        contract_scripthash = Hash160Str.from_str_or_int(contract_scripthash) or self.contract_scripthash
        return self.meta_rpc_method("setsourcecodebreakpoints", [contract_scripthash, filename, line_num])

    def set_source_code_breakpoints(self, filename_and_line_num: List[Union[str, int]], contract_scripthash: Union[str, int, Hash160Str] = None):
        contract_scripthash = Hash160Str.from_str_or_int(contract_scripthash) or self.contract_scripthash
        return self.meta_rpc_method("setsourcecodebreakpoints", [contract_scripthash] + filename_and_line_num)

    def list_source_code_breakpoints(self, contract_scripthash: Union[str, int, Hash160Str] = None):
        contract_scripthash = Hash160Str.from_str_or_int(contract_scripthash) or self.contract_scripthash
        return self.meta_rpc_method("listsourcecodebreakpoints", [contract_scripthash])

    def delete_source_code_breakpoint(self, filename: str, line_num: int, contract_scripthash: Union[str, int, Hash160Str] = None):
        contract_scripthash = Hash160Str.from_str_or_int(contract_scripthash) or self.contract_scripthash
        return self.meta_rpc_method("deletesourcecodebreakpoints", [contract_scripthash, filename, line_num])

    def delete_source_code_breakpoints(self, filename_and_line_num: List[Union[str, int]] = None, contract_scripthash: Union[str, int, Hash160Str] = None):
        contract_scripthash = Hash160Str.from_str_or_int(contract_scripthash) or self.contract_scripthash
        filename_and_line_num = filename_and_line_num or []
        return self.meta_rpc_method("deletesourcecodebreakpoints", [contract_scripthash] + filename_and_line_num)

    def delete_debug_snapshots(self, fairy_sessions: Union[List[str], str]):
        if type(fairy_sessions) is str:
            return self.meta_rpc_method("deletedebugsnapshots", [fairy_sessions])
        return self.meta_rpc_method("deletedebugsnapshots", fairy_sessions)

    def list_debug_snapshots(self):
        return self.meta_rpc_method("listdebugsnapshots", [])

    def get_method_by_instruction_pointer(self, instruction_pointer: int, scripthash: Union[str, int, Hash160Str] = None):
        scripthash = Hash160Str.from_str_or_int(scripthash) or self.contract_scripthash
        return self.meta_rpc_method("getmethodbyinstructionpointer", [scripthash, instruction_pointer])

    def debug_any_function_with_session(self, scripthash: Union[str, int, Hash160Str], operation: str,
                                       params: List[Union[str, int, dict, Hash160Str, UInt160, bytes, bytearray]] = None,
                                       signers: Union[Signer, List[Signer]] = None, relay: bool = None,
                                       with_print=True, fairy_session: str = None) -> RpcBreakpoint:
        scripthash = Hash160Str.from_str_or_int(scripthash) or self.contract_scripthash
        fairy_session = fairy_session or self.fairy_session
        if self.with_print and with_print:
            if fairy_session:
                print(f'{fairy_session}::debugfunction {operation}{params}')
            else:
                print(f'debugfunction {operation}{params}')
    
        params = params or []
        signers = to_list(signers or self.signers)
        parameters = [
            str(scripthash),
            operation,
            list(map(lambda param: self.parse_param(param), params)),
            list(map(lambda signer: signer.to_dict(), signers)),
        ]
        raw_result = self.meta_rpc_method_with_raw_result(
            'debugfunctionwithsession',
            [fairy_session, relay or (relay is None and self.function_default_relay)] + parameters)
        result = raw_result['result']
        return RpcBreakpoint(result['state'], result['breakreason'],
                             result['scripthash'], result['contractname'], result['instructionpointer'],
                             result['sourcefilename'], result['sourcelinenum'], result['sourcecontent'],
                             exception=result['exception'], result_stack=self.parse_stack_from_raw_result(raw_result))

    def debug_function_with_session(self, operation: str,
                                        params: List[Union[List, str, int, dict, Hash160Str, UInt160, bytes, bytearray]] = None,
                                        signers: List[Signer] = None, relay: bool = None,
                                        with_print=True, fairy_session: str = None) -> RpcBreakpoint:
        return self.debug_any_function_with_session(
            self.contract_scripthash, operation,
            params=params, signers=signers, relay=relay,
            with_print=with_print, fairy_session=fairy_session)
    
    def debug_script_with_session(self, script_base64_encoded: Union[str, bytes],
                                  signers: Union[Signer, List[Signer]] = None, relay: bool = None,
                                  with_print = True, fairy_session: str = None) -> RpcBreakpoint:
        fairy_session = fairy_session or self.fairy_session
        signers = signers or self.signers
        if type(script_base64_encoded) is bytes:
            script_base64_encoded: str = script_base64_encoded.decode()
        if self.with_print and with_print:
            if fairy_session:
                print(f'{fairy_session}::debugscript {script_base64_encoded}')
            else:
                print(f'debugfunction {script_base64_encoded}')
        raw_result = self.meta_rpc_method_with_raw_result(
            'debugscriptwithsession',
            [fairy_session, relay or (relay is None and self.function_default_relay),
             script_base64_encoded, list(map(lambda signer: signer.to_dict(), signers))])
        result = raw_result['result']
        return RpcBreakpoint(result['state'], result['breakreason'],
                             result['scripthash'], result['contractname'], result['instructionpointer'],
                             result['sourcefilename'], result['sourcelinenum'], result['sourcecontent'],
                             exception=result['exception'], result_stack=self.parse_stack_from_raw_result(raw_result))

    def debug_continue(self, fairy_session: str = None) -> RpcBreakpoint:
        fairy_session = fairy_session or self.fairy_session
        result = self.meta_rpc_method_with_raw_result("debugcontinue", [fairy_session])
        return RpcBreakpoint.from_raw_result(result)

    def debug_continue_to_instruction_address(self, instruction_address: int,
            contract_scripthash: Union[str, int, Hash160Str] = None, fairy_session: str = None) -> RpcBreakpoint:
        has_breakpoint: bool = instruction_address in self.list_assembly_breakpoints(contract_scripthash=contract_scripthash)
        if not has_breakpoint:
            self.set_assembly_breakpoints(instruction_address, contract_scripthash=contract_scripthash)
        result = self.debug_continue(fairy_session=fairy_session)
        if not has_breakpoint:
            self.delete_assembly_breakpoints(instruction_address, contract_scripthash=contract_scripthash)
        return result

    def debug_step_into(self, fairy_session: str = None) -> RpcBreakpoint:
        fairy_session = fairy_session or self.fairy_session
        result = self.meta_rpc_method_with_raw_result("debugstepinto", [fairy_session])
        return RpcBreakpoint.from_raw_result(result)

    def debug_step_out(self, fairy_session: str = None) -> RpcBreakpoint:
        fairy_session = fairy_session or self.fairy_session
        result = self.meta_rpc_method_with_raw_result("debugstepout", [fairy_session])
        return RpcBreakpoint.from_raw_result(result)

    def debug_step_over(self, fairy_session: str = None) -> RpcBreakpoint:
        fairy_session = fairy_session or self.fairy_session
        result = self.meta_rpc_method_with_raw_result("debugstepover", [fairy_session])
        return RpcBreakpoint.from_raw_result(result)

    def debug_step_over_source_code(self, fairy_session: str = None) -> RpcBreakpoint:
        fairy_session = fairy_session or self.fairy_session
        result = self.meta_rpc_method_with_raw_result("debugstepoversourcecode", [fairy_session])
        return RpcBreakpoint.from_raw_result(result)

    def debug_step_over_assembly(self, fairy_session: str = None) -> RpcBreakpoint:
        fairy_session = fairy_session or self.fairy_session
        result = self.meta_rpc_method_with_raw_result("debugstepoverassembly", [fairy_session])
        return RpcBreakpoint.from_raw_result(result)

    def get_invocation_stack(self, fairy_session: str = None):
        fairy_session = fairy_session or self.fairy_session
        return self.meta_rpc_method("getinvocationstack", [fairy_session])

    def get_local_variables(self, invocation_stack_index: int = 0, fairy_session: str = None) -> Any:
        fairy_session = fairy_session or self.fairy_session
        result = self.meta_rpc_method_with_raw_result("getlocalvariables", [fairy_session, invocation_stack_index])
        return self.parse_stack_from_raw_result(result)

    def get_arguments(self, invocation_stack_index: int = 0, fairy_session: str = None) -> Any:
        fairy_session = fairy_session or self.fairy_session
        result = self.meta_rpc_method_with_raw_result("getarguments", [fairy_session, invocation_stack_index])
        return self.parse_stack_from_raw_result(result)

    def get_static_fields(self, invocation_stack_index: int = 0, fairy_session: str = None) -> Any:
        fairy_session = fairy_session or self.fairy_session
        result = self.meta_rpc_method_with_raw_result("getstaticfields", [fairy_session, invocation_stack_index])
        return self.parse_stack_from_raw_result(result)

    def get_evaluation_stack(self, invocation_stack_index: int = 0, fairy_session: str = None) -> Any:
        fairy_session = fairy_session or self.fairy_session
        result = self.meta_rpc_method_with_raw_result("getevaluationstack", [fairy_session, invocation_stack_index])
        return self.parse_stack_from_raw_result(result)

    def get_instruction_pointer(self, invocation_stack_index: int = 0, fairy_session: str = None) -> Any:
        fairy_session = fairy_session or self.fairy_session
        result = self.meta_rpc_method_with_raw_result("getinstructionpointer", [fairy_session, invocation_stack_index])
        return self.parse_stack_from_raw_result(result)[0]

    def get_variable_value_by_name(self, variable_name: str, invocation_stack_index: int = 0, fairy_session: str = None) -> Any:
        fairy_session = fairy_session or self.fairy_session
        result = self.meta_rpc_method_with_raw_result("getvariablevaluebyname", [fairy_session, variable_name, invocation_stack_index])
        return self.parse_stack_from_raw_result(result)

    def get_variable_names_and_values(self, invocation_stack_index: int = 0, fairy_session: str = None) -> Any:
        fairy_session = fairy_session or self.fairy_session
        result = self.meta_rpc_method_with_raw_result("getvariablenamesandvalues", [fairy_session, invocation_stack_index])
        return self.parse_stack_from_raw_result(result)
    
    def get_contract_opcode_coverage(self, scripthash: UInt160 = None) -> Dict[int, bool]:
        scripthash = scripthash or self.contract_scripthash
        result: Dict[str, bool] = self.meta_rpc_method_with_raw_result("getcontractopcodecoverage", [scripthash])['result']
        return {int(k): v for k, v in result.items()}

    def get_contract_source_code_coverage(self, scripthash: UInt160 = None) -> Dict[str, Dict[str, bool]]:
        scripthash = scripthash or self.contract_scripthash
        result: Dict[str, Dict[str, bool]] = self.meta_rpc_method_with_raw_result("getcontractsourcecodecoverage", [scripthash])['result']
        return result

    def clear_contract_opcode_coverage(self, scripthash: UInt160 = None) -> Dict[int, bool]:
        scripthash = scripthash or self.contract_scripthash
        result: Dict[str, bool] = self.meta_rpc_method_with_raw_result("clearcontractopcodecoverage", [scripthash])['result']
        return {int(k): v for k, v in result.items()}
