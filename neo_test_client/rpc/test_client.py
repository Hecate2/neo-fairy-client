from typing import List, Union, Dict, Any
import base64
import json
import requests
from retry import retry

from neo_test_client.utils.types import Hash160Str, Hash256Str, PublicKeyStr, Signer
from neo3.core.types import UInt160, UInt256
from neo3.contracts import NeoToken, GasToken

neo, gas = NeoToken(), GasToken()

RequestExceptions = (
    requests.RequestException,
    requests.ConnectionError,
    requests.HTTPError,
    requests.Timeout,
)
request_timeout = None  # 20


class TestClient:
    def __init__(self, target_url: str, contract_scripthash: Hash160Str,
                 wallet_address: str, wallet_path: str, wallet_password: str, signer: Signer = None,
                 with_print=True, requests_session=requests.Session(), verbose_return=False,
                 function_default_relay=True, script_default_relay=False,
                 rpc_server_session: str = None):
        """

        :param target_url: url to the rpc server affliated to neo-cli
        :param wallet_address: address of your wallet (starting with 'N'); "NVbGwMfRQVudTjWAUJwj4K68yyfXjmgbPp"
        :param wallet_path: 'wallets/dev.json'
        :param wallet_password: '12345678'
        :param requests_session: requests.Session
        :param verbose_return: return result, raw_result, post_data.
            This is to avoid reading previous_result for concurrency safety.
            For concurrency, set verbose_return=True
        """
        self.target_url = target_url
        self.contract_scripthash = contract_scripthash
        self.requests_session = requests_session
        self.wallet_address = wallet_address
        wallet_scripthash = Hash160Str.from_address(wallet_address)
        self.wallet_scripthash = wallet_scripthash
        self.signer = signer or Signer(wallet_scripthash)
        self.wallet_path = wallet_path
        self.wallet_password = wallet_password
        self.previous_post_data = None
        self.with_print = with_print
        self.previous_raw_result = None
        self.previous_result = None
        self.previous_txBase64Str = None
        self.previous_gas_consumed: int = None
        self.previous_network_fee: int = None
        self.verbose_return = verbose_return
        self.function_default_relay = function_default_relay
        self.script_default_relay = script_default_relay
        self.rpc_server_session = rpc_server_session
    
    @staticmethod
    def request_body_builder(method, parameters: List):
        return json.dumps({
            "jsonrpc": "2.0",
            "method": method,
            "params": parameters,
            "id": 1,
        }, separators=(',', ':'))
    
    @staticmethod
    def bytes_to_UInt160(bytestring: bytes):
        return Hash160Str.from_UInt160(UInt160.deserialize_from_bytes(bytestring))
    
    @staticmethod
    def base64_struct_to_bytestrs(base64_struct: dict) -> List[bytes]:
        processed_struct = []
        if type(base64_struct) is dict and 'type' in base64_struct and base64_struct['type'] == 'Struct':
            values = base64_struct['value']
            for value in values:
                if value['type'] == 'ByteString':
                    processed_struct.append(base64.b64decode(value['value']))
        return processed_struct
    
    @retry(RequestExceptions, tries=2, logger=None)
    def meta_rpc_method(self, method: str, parameters: List, relay: bool = None, do_not_raise_on_result=False) -> Any:
        post_data = self.request_body_builder(method, parameters)
        self.previous_post_data = post_data
        result = json.loads(self.requests_session.post(self.target_url, post_data, timeout=request_timeout).text)
        if 'error' in result:
            raise ValueError(result['error']['message'])
        if type(result['result']) is dict:
            result_result: dict = result['result']
            self.previous_gas_consumed = int(result_result.get('gasconsumed', 0)) or None
            self.previous_network_fee = int(result_result.get('networkfee', 0)) or None
            if 'exception' in result_result and result_result['exception'] is not None:
                if do_not_raise_on_result:
                    return result_result['exception']
                else:
                    print(post_data)
                    print(result)
                    raise ValueError(result_result['exception'])
            if relay or (relay is None and self.function_default_relay):
                if method in {'invokefunction', 'invokescript'} and 'tx' not in result_result:
                    raise ValueError('No `tx` in response. '
                                     'Did you call `client.openwallet()` before `invokefunction`?')
                if 'tx' in result_result:
                    tx = result_result['tx']
                    self.previous_txBase64Str = tx
                    self.sendrawtransaction(tx)
                # else:
                #     self.previous_txBase64Str = None
        self.previous_raw_result = result
        self.previous_result = self.parse_raw_result(result)
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
    
    def getrawtransaction(self, transaction_hash: Hash256Str, verbose: bool = False):
        return self.meta_rpc_method("getrawtransaction", [str(transaction_hash), verbose], relay=False)
    
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
    
    def openwallet(self, path: str = None, password: str = None) -> dict:
        """
        WARNING: usually you should use this method along with __init__.
        Use another TestClient object to open another wallet
        """
        if not path:
            path = self.wallet_path
        if not password:
            password = self.wallet_password
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

    @staticmethod
    def parse_raw_result(raw_result: dict):
        def parse_single_item(item: Union[Dict, List]):
            if 'iterator' in item:
                item = item['iterator']
                if item:
                    if type(item[0]['value']) is not list:
                        return [parse_single_item(i) for i in item]
                    else:
                        return {parse_single_item(i['value'][0]): parse_single_item(i['value'][1]) for i in item}
                else:
                    assert item == []
                    return item
            _type = item['type']
            if _type == 'Any' and 'value' not in item:
                return None
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
                return [parse_single_item(i) for i in value]
            elif _type == 'Struct':
                return tuple([parse_single_item(i) for i in value])
            elif _type == 'Map':
                return {parse_single_item(i['key']): parse_single_item(i['value']) for i in value}
            elif _type == 'Pointer':
                return int(value)
            else:
                raise ValueError(f'Unknown type {_type}')
        
        result: Dict = raw_result['result']
        if type(result) is not dict or 'stack' not in result:
            return result
        if not result['stack']:
            return result['stack']
        result: List = result['stack'][0]
        return parse_single_item(result)
    
    @classmethod
    def parse_params(cls, param: Union[str, int, dict, Hash160Str, UInt160, UInt256, bytes]) -> Dict[str, str]:
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
        elif type_param is bytes:
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
                'value': [cls.parse_params(param_) for param_ in param]
            }
        elif type_param is dict:
            return {
                'type': 'Map',
                'value': [{'key': cls.parse_params(k), 'value': cls.parse_params(v)} for k, v in param.items()]
            }
        elif param is None:
            return {
                'type': 'Any',
            }
        raise ValueError(f'Unable to handle param {param} with type {type_param}')
    
    def invokefunction_of_any_contract(self, scripthash: Hash160Str, operation: str,
                                       params: List[Union[str, int, dict, Hash160Str, UInt160]] = None,
                                       signers: List[Signer] = None, relay: bool = None, do_not_raise_on_result=False,
                                       with_print=True, rpc_server_session: str = None) -> Any:
        rpc_server_session = rpc_server_session or self.rpc_server_session
        if self.with_print and with_print:
            if rpc_server_session:
                print(f'{rpc_server_session}::invokefunction {operation}')
            else:
                print(f'invokefunction {operation}')
        
        if not params:
            params = []
        if not signers:
            signers = [self.signer]
        parameters = [
            str(scripthash),
            operation,
            list(map(lambda param: self.parse_params(param), params)),
            list(map(lambda signer: signer.to_dict(), signers)),
        ]
        if rpc_server_session:
            result = self.meta_rpc_method(
                'invokefunctionwithsession', [rpc_server_session, relay or (relay is None and self.function_default_relay)] + parameters, relay=False,
                do_not_raise_on_result=do_not_raise_on_result)
        else:
            result = self.meta_rpc_method('invokefunction', parameters, relay=relay,
                                          do_not_raise_on_result=do_not_raise_on_result)
        return result
    
    def invokefunction(self, operation: str, params: List[Union[str, int, Hash160Str, UInt160]] = None,
                       signers: List[Signer] = None, relay: bool = None, do_not_raise_on_result=False, with_print=True,
                       rpc_server_session: str = None) -> Any:
        return self.invokefunction_of_any_contract(self.contract_scripthash, operation, params,
                                                   signers=signers, relay=relay or (relay is None and self.function_default_relay),
                                                   do_not_raise_on_result=do_not_raise_on_result,
                                                   with_print=with_print, rpc_server_session=rpc_server_session)
    
    def invokescript(self, script: Union[str, bytes], signers: List[Signer] = None, relay: bool = None,
                     rpc_server_session: str = None) -> Any:
        if type(script) is bytes:
            script: str = script.decode()
        if not signers:
            signers = [self.signer]
        rpc_server_session = rpc_server_session or self.rpc_server_session
        if rpc_server_session:
            relay = relay or (relay is None and self.script_default_relay)
            result = self.meta_rpc_method(
                'invokescriptwithsession',
                [rpc_server_session, relay, script, list(map(lambda signer: signer.to_dict(), signers))],
                relay=False)
        else:
            result = self.meta_rpc_method(
                'invokescript',
                [script, list(map(lambda signer: signer.to_dict(), signers))],
                relay=relay)
        return result
    
    def sendfrom(self, asset_id: Hash160Str, from_address: str, to_address: str, value: int,
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
        if not signers:
            signers = [self.signer]
        return self.meta_rpc_method('sendfrom', [
            asset_id.to_str(),
            from_address, to_address, value,
            signers
        ])
    
    def sendtoaddress(self, asset_id: Hash160Str, address, value: int):
        return self.meta_rpc_method('sendtoaddress', [
            asset_id.string, address, value,
        ])
    
    def send_neo_to_address(self, to_address: Hash160Str, value: int):
        return self.sendtoaddress(Hash160Str.from_UInt160(neo.hash), to_address, value)
    
    def send_gas_to_address(self, to_address: Hash160Str, value: int):
        return self.sendtoaddress(Hash160Str.from_UInt160(gas.hash), to_address, value)
    
    def getwalletbalance(self, asset_id: Hash160Str) -> int:
        return int(self.meta_rpc_method('getwalletbalance', [asset_id.to_str()])['balance'])
    
    def get_neo_balance(self, owner: Hash160Str = None, with_print=False) -> int:
        return self.invokefunction_of_any_contract(Hash160Str.from_UInt160(neo.hash), 'balanceOf', params=[owner or self.wallet_scripthash], relay=False, with_print=with_print)
        # return self.getwalletbalance(Hash160Str.from_UInt160(NeoToken().hash))

    def get_gas_balance(self, owner: Hash160Str = None, with_print=False) -> int:
        return self.invokefunction_of_any_contract(Hash160Str.from_UInt160(gas.hash), 'balanceOf', params=[owner or self.wallet_scripthash], relay=False, with_print=with_print)
        # return self.getwalletbalance(Hash160Str.from_UInt160(GasToken().hash))
    
    def get_nep17token_balance(self, token_address: Hash160Str, owner: Hash160Str = None, with_print=False):
        return self.invokefunction_of_any_contract(token_address, "balanceOf", params=[owner or self.wallet_scripthash], relay=False, with_print=with_print)

    def get_nep11token_balance(self, token_address: Hash160Str, tokenId: Union[bytes, str, int], owner: Hash160Str = None, with_print=False):
        return self.invokefunction_of_any_contract(token_address, "balanceOf", params=[owner or self.wallet_scripthash, tokenId], relay=False, with_print=with_print)

    def new_snapshots_from_current_system(self, rpc_server_sessions: Union[List[str], str] = None):
        if type(rpc_server_sessions) is str:
            return self.meta_rpc_method("newsnapshotsfromcurrentsystem", [rpc_server_sessions])
        if rpc_server_sessions is None:
            if self.rpc_server_session:
                return self.meta_rpc_method("newsnapshotsfromcurrentsystem", [self.rpc_server_session])
            raise ValueError('No RpcServer session specified')
        return self.meta_rpc_method("newsnapshotsfromcurrentsystem", rpc_server_sessions)
    
    def delete_snapshots(self, rpc_server_sessions: Union[List[str], str]):
        if type(rpc_server_sessions) is str:
            return self.meta_rpc_method("deletesnapshots", [rpc_server_sessions])
        return self.meta_rpc_method("deletesnapshots", rpc_server_sessions)
    
    def list_snapshots(self):
        return self.meta_rpc_method("listsnapshots", [])
    
    def rename_snapshot(self, old_name: str, new_name: str):
        return self.meta_rpc_method("renamesnapshot", [old_name, new_name])
    
    def copy_snapshot(self, old_name: str, new_name: str):
        return self.meta_rpc_method("copysnapshot", [old_name, new_name])
    
    def set_snapshot_timestamp(self, timestamp_ms: int, rpc_server_session: str = None):
        if rpc_server_session is None:
            if self.rpc_server_session is None:
                raise ValueError('No RpcServer session specified')
            rpc_server_session = self.rpc_server_session
        return self.meta_rpc_method("setsnapshottimestamp", [rpc_server_session, timestamp_ms])
    
    def get_snapshot_timestamp(self, rpc_server_sessions: Union[List[str], str]):
        if type(rpc_server_sessions) is str:
            return self.meta_rpc_method("getsnapshottimestamp", [rpc_server_sessions])
        return self.meta_rpc_method("getsnapshottimestamp", rpc_server_sessions)

    def virtual_deploy(self, rpc_server_session: str, nef: bytes, manifest: str):
        return Hash160Str(self.meta_rpc_method("virtualdeploy", [rpc_server_session, base64.b64encode(nef).decode(), manifest])[rpc_server_session])
