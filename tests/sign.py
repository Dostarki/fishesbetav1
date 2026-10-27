import sys
from eth_account import Account
from eth_account.messages import encode_defunct
key, msg = sys.argv[1], sys.argv[2]
if msg.startswith('0x'):
    msg = bytes.fromhex(msg[2:]).decode()
s = Account.sign_message(encode_defunct(text=msg), key).signature.hex()
print(s if s.startswith('0x') else '0x' + s)
