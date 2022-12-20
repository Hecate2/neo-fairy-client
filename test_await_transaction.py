import traceback
import time
from neo_fairy_client import FairyClient
from neo_fairy_client.utils import Hash256Str

client = FairyClient()
print(client.await_confirmed_transaction(Hash256Str('0x9861ed20088d360d1906e8671634e840e74012050efb2c4aa8b6a9e84b459141')))  # exists on mainnet
print(start_time := time.time())
try:
    print(client.await_confirmed_transaction(Hash256Str('0x9861ed20088d360d1906e8671634e840e74012050efb2c4aa8b6a9e84b459140')))
except ValueError:
    traceback.print_exc()
print(time.time() - start_time)