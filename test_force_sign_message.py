import neo_fairy_client
from neo_fairy_client import FairyClient, NamedCurveHash

c = FairyClient(target_url='http://localhost:16868', fairy_session='force sign message', auto_preparation=False)
msg = b'a'
for namedCurveHash in NamedCurveHash.secp256r1SHA256, NamedCurveHash.secp256r1Keccak256:
    print(sig := c.force_sign_message(msg, namedCurveHash))
    result = c.invokefunction_of_any_contract(
        neo_fairy_client.CryptoLibAddress,
        'verifyWithECDsa',
        [msg, neo_fairy_client.defaultFairyWalletPublicKeySecp256R1, sig, namedCurveHash])
    assert result is True
    assert c.force_verify_with_ecdsa(msg, neo_fairy_client.defaultFairyWalletPublicKeySecp256R1, sig, namedCurveHash) is True
for namedCurveHash in NamedCurveHash.secp256k1SHA256, NamedCurveHash.secp256k1Keccak256:
    print(sig := c.force_sign_message(msg, namedCurveHash))
    result = c.force_verify_with_ecdsa(msg, neo_fairy_client.defaultFairyWalletPublicKeySecp256K1, sig, namedCurveHash)
    assert result is True
print(sig := c.force_sign_message(msg))
result = c.invokefunction_of_any_contract(
    neo_fairy_client.CryptoLibAddress,
    'verifyWithECDsa',
    [msg, neo_fairy_client.defaultFairyWalletPublicKeySecp256R1, sig, NamedCurveHash.secp256r1SHA256])
assert result is True
