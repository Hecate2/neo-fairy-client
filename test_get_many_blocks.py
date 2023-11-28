from neo_fairy_client import FairyClient, Hash160Str

client = FairyClient()
start, end = 3080019, 3080932
results = client.get_many_blocks([start, end])
assert len(results) == end - start + 1
