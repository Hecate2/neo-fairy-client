from neo_fairy_client.utils.types import Hash160Str, Hash256Str, PublicKeyStr, Signer, WitnessScope
from neo_fairy_client.utils.interpreters import Interpreter
from neo_fairy_client.utils.misc import to_list

from neo3.contracts import (PolicyContract, NeoToken, GasToken, OracleContract, DesignationContract, ManagementContract, LedgerContract, CryptoContract, StdLibContract)
PolicyAddress = Hash160Str.from_UInt160(PolicyContract().hash)
NeoAddress = Hash160Str.from_UInt160(NeoToken().hash)
GasAddress = Hash160Str.from_UInt160(GasToken().hash)
OracleAddress = Hash160Str.from_UInt160(OracleContract().hash)
DesignationAddress = Hash160Str.from_UInt160(DesignationContract().hash)
ManagementAddress = Hash160Str.from_UInt160(ManagementContract().hash)
LedgerAddress = Hash160Str.from_UInt160(LedgerContract().hash)
CryptoLibAddress = Hash160Str.from_UInt160(CryptoContract().hash)
StdLibAddress = Hash160Str.from_UInt160(StdLibContract().hash)
