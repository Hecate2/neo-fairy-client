from typing import List, Union
from enum import Enum
from neo_fairy_client.utils.timers import gen_timestamp_and_date_str_in_seconds, gen_timestamp_and_date_str_in_days
from neo_fairy_client.utils.misc import to_list

import time
from neo3.core.types import UInt160, UInt256
from neo3.wallet import Account


class HashStr(str):
    def __init__(self, string: str):
        super(HashStr, self).__init__()
        # check length of string here
        # assert string.startswith('0x')
        self.string = string
    
    def to_str(self):
        return self.string
    
    def __str__(self):
        return self.string
    
    def __repr__(self):
        return self.string
    
    def __eq__(self, other):
        if isinstance(other, HashStr):
            return self.string == other.string
        return False

    def __ne__(self, other):
        if isinstance(other, HashStr):
            return self.string != other.string
        return True

    def __hash__(self):
        return hash(self.string)


class Hash256Str(HashStr):
    """
    0x59916d8c2fc5feb06b77aec289ac34b49ae3bccb1f88fe64ea5172c79fc1af05
    """

    def __init__(self, string: Union[str, UInt256]):
        # assert string.startswith('0x')
        if type(string) is UInt256:
            string = bytearray(string._data)
            string.reverse()
            string = string.hex()
        if len(string) == 64:
            string = '0x' + string
        assert len(string) == 66
        super().__init__(string)

    @classmethod
    def from_UInt256(cls, u: UInt256):
        u_bytearray = bytearray(u._data)
        u_bytearray.reverse()
        hash256str = u_bytearray.hex()
        return cls(hash256str)

    @classmethod
    def zero(cls):
        return cls(UInt256.zero())

    def to_UInt256(self):
        return UInt256.from_string(self.string[2:])


class Hash160Str(HashStr):
    """
    0xf61eebf573ea36593fd43aa150c055ad7906ab83
    """
    
    def __init__(self, string: Union[str, UInt160]):
        # assert string.startswith('0x')
        if type(string) is UInt160:
            string = bytearray(string._data)
            string.reverse()
            string = string.hex()
        if len(string) == 40:
            string = '0x' + string
        assert len(string) == 42
        super().__init__(string)
    
    @classmethod
    def from_UInt160(cls, u: UInt160):
        u_bytearray = bytearray(u._data)
        u_bytearray.reverse()
        hash160str = u_bytearray.hex()
        return cls(hash160str)

    @classmethod
    def from_address(cls, address: str):
        return cls.from_UInt160(Account.address_to_script_hash(address))

    @classmethod
    def zero(cls):
        return cls(UInt160.zero())

    def to_UInt160(self):
        return UInt160.from_string(self.string[2:])
    
    def to_address(self):
        return Account.script_hash_to_address(self.to_UInt160())


class PublicKeyStr(HashStr):
    """
    03f6829c418b7272efa93b19cc3336506fb84efac6a758be3d6d5216d0fbc4d6dd
    """
    def __init__(self, string: str):
        assert len(string) == 66
        super().__init__(string)


class WitnessScope(Enum):
    NONE = 'None'  # no contract has your valid signature
    CalledByEntry = 'CalledByEntry'  # only the called contract has your valid signature
    Global = 'Global'  # all contracts have your valid signature
    CustomContracts = 'CustomContracts'  # only contracts of designated addresses have your valid signature
    CustomGroups = 'CustomGroups'  # only designated public keys have your valid signature
    WitnessRules = 'WitnessRules'  # complex rules to determine which contracts have your valid signature
    # https://docs.neo.org/docs/en-us/basic/concept/transaction.html#witnessrule


class Signer:
    def __init__(self, account: Union[Hash160Str, str], scopes: WitnessScope = WitnessScope.CalledByEntry,
                 allowedcontracts: Union[List[Hash160Str], Hash160Str] = None,
                 allowedgroups: Union[List[PublicKeyStr], PublicKeyStr] = None,
                 rules: Union[List[dict], dict] = None):
        self.account: Hash160Str = account if type(account) is Hash160Str else Hash160Str.from_address(account)
        self.scopes: WitnessScope = scopes
        if self.scopes == WitnessScope.CustomContracts and not allowedcontracts:
            print('WARNING! You did not allow any contract to use your signature.')
        if self.scopes == WitnessScope.CustomGroups and not allowedgroups:
            print('WARNING! You did not allow any public key account to use your signature.')
        if self.scopes == WitnessScope.WitnessRules and not rules:
            raise ValueError('WARNING! No rules written for WitnessRules')
        self.allowedcontracts = to_list(allowedcontracts)
        self.allowedgroups = to_list(allowedgroups)
        self.rules = to_list(rules)
    
    def to_dict(self):
        return {
            'account': str(self.account),
            'scopes': self.scopes.value,
            'allowedcontracts': self.allowedcontracts,
            'allowedgroups': self.allowedgroups,
            'rules': self.rules
        }


if __name__ == '__main__':
    print('30 days:', gen_timestamp_and_date_str_in_days(30))
    print(' 0 days:', gen_timestamp_and_date_str_in_days(0))
    print('time now:', time.time() * 1000)
    print(' 5 secs:', gen_timestamp_and_date_str_in_seconds(5))
