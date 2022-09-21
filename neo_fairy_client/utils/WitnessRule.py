from neo_fairy_client.utils.types import Hash160Str, PublicKeyStr


def Allow(bool_: dict):
    return {
        "action": "Allow",
        "condition": bool_
    }


def Deny(bool_: dict):
    return {
        "action": "Deny",
        "condition": bool_
    }


def Not(condition: dict):
    return {
        "type": "Not",
        "expression": condition
    }


def And(*conditions):
    return {
        "type": "And",
        "expressions": list(conditions)
    }


def Or(*conditions):
    return {
        "type": "Or",
        "expressions": list(conditions)
    }


def ScriptHash(scripthash: Hash160Str):
    return {
        "type": "ScriptHash",
        "hash": scripthash.to_str()
    }


def Group(publickey: PublicKeyStr):
    return {
        "type": "Group",
        "group": publickey.to_str()
    }


def CalledByEntry():
    return {
        "type": "CalledByEntry",
    }


def CalledByContract(scripthash: Hash160Str):
    return {
        "type": "CalledByContract",
        "hash": scripthash.to_str()
    }


def CalledByGroup(publickey: PublicKeyStr):
    return {
        "type": "CalledByGroup",
        "group": publickey.to_str()
    }


def True_():
    return {"type": "Boolean", "expression": True}


def False_():
    return {"type": "Boolean", "expression": False}
