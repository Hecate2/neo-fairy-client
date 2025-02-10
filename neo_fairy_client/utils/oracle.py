from neo_fairy_client.utils.types import Hash160Str, UInt160, Hash256Str, UInt256
from base64 import b64decode
from typing import List, Dict, Union
from enum import Enum


class OracleRequest:
    def __init__(self, json_request: Union[Dict, List[Dict[str, str]]]):
        """
        :param json_request: FairyClient.previous_raw_result['result']['oraclerequests'][0]['value']; [{'type': 'ByteString', 'value': 'SE6A2KnUVd35l1Qxfp+rF5yMGroU/NYEUMb6ExEqzMM='}, {'type': 'Integer', 'value': '100000000'}, {'type': 'ByteString', 'value': 'aHR0cHM6Ly93d3cuYmluYW5jZS5jb20vYXBpL3YzL3RpY2tlci9wcmljZT9zeW1ib2w9TkVPVVNEVA=='}, {'type': 'ByteString', 'value': 'cHJpY2U='}, {'type': 'ByteString', 'value': '23U0WL/JySWJDctjIIFqfB+0h+8='}, {'type': 'ByteString', 'value': 'Y2FsbGJhY2s='}, {'type': 'ByteString', 'value': 'KAx0ZXN0VXNlckRhdGE='}]
        """
        if type(json_request) is dict and json_request['type'] == 'Array':
            json_request: List[Dict[str, str]] = json_request['value']
        self.original_tx_id: Hash256Str = Hash256Str(UInt256(b64decode(json_request[0]['value'])))
        self.gas_for_response: int = int(json_request[1]['value'])
        self.url: str = b64decode(json_request[2]['value']).decode()
        self.filter: str = b64decode(json_request[3]['value']).decode()  # json path filter string
        self.callback_contract: Hash160Str = Hash160Str(UInt160(b64decode(json_request[4]['value'])))
        self.callback_method: str = b64decode(json_request[5]['value']).decode()
        self.user_data: bytes = b64decode(json_request[6]['value'])
        if len(json_request) > 7:
            self.request_id: Union[int, None] = int(json_request[7]['value'])
        else:
            self.request_id = None


class OracleResponseCode(Enum):
    """Enum for Oracle Response Codes."""
    # Indicates that the request has been successfully completed.
    Success = 0x00
    # Indicates that the protocol of the request is not supported.
    ProtocolNotSupported = 0x10
    # Indicates that the oracle nodes cannot reach a consensus on the result of the request.
    ConsensusUnreachable = 0x12
    # Indicates that the requested Uri does not exist.
    NotFound = 0x14
    # Indicates that the request was not completed within the specified time.
    Timeout = 0x16
    # Indicates that there is no permission to request the resource.
    Forbidden = 0x18
    # Indicates that the data for the response is too large.
    ResponseTooLarge = 0x1a
    # Indicates that the request failed due to insufficient balance.
    InsufficientFunds = 0x1c
    # Indicates that the content-type of the request is not supported.
    ContentTypeNotSupported = 0x1f
    # Indicates that the request failed due to other errors.
    Error = 0xff
