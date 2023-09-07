from neo_fairy_client import FairyClient, ContractManagementAddress, Hash160Str

c = FairyClient(contract_scripthash=ContractManagementAddress)
print(c.list_contracts())