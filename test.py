from dotenv import load_dotenv
from os import getenv
import json


from web3 import Web3  # // Link to docs: https://shorturl.at/agMQX // #
from eth_account import Account  # // Link to docs: https://shorturl.at/sHW39 // #
from eth_account.signers.local import LocalAccount
from eth_typing import (  # // Link to docs: https://shorturl.at/cBJ28 // #
    ChecksumAddress,
    TypeStr,
)

load_dotenv(".env")

PRIVATEKEY: str = getenv("PRIVATE_KEY")  # type: ignore
PUBLICKEY: str = getenv("PUBLIC_KEY")  # type: ignore
with open(getenv("PATH_TO_UNI_LP_ABI")) as uniLP_abi:  # type: ignore
    uniLPABI: TypeStr = json.load(uniLP_abi)
with open(getenv("PATH_TO_UNI_FACT_ABI")) as uniFact_abi:  # type: ignore
    uniFactABI: TypeStr = json.load(uniFact_abi)
with open(getenv("PATH_TO_UNI_ROUTER_ABI")) as uniRout_abi:  # type: ignore
    uniRouterABI: TypeStr = json.load(uniRout_abi)

UNITOKEN: ChecksumAddress = Web3.to_checksum_address(
    "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984"
)

WETHADDRESS: ChecksumAddress = Web3.to_checksum_address(
    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
)

w3: Web3 = Web3(
    Web3.HTTPProvider("https://goerli.infura.io/v3/e1be908a63b34bd0aae2620578ef7f0a")
)

print(w3.is_connected())


account: LocalAccount = Account.from_key(PRIVATEKEY)

print(account.address)

routeraddress: ChecksumAddress = Web3.to_checksum_address(
    "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"  # Uniswap Router Address
)

router = w3.eth.contract(address=routeraddress, abi=uniRouterABI)

# tx_hash = w3.eth.send_transaction(
#     {"from": account.address, "to": "0x36334Fc30798F77a880e26850BDCB3D167E91807", "value": 100000}  # type: ignore
# )


transaction = {
    "chainId": w3.eth.chain_id,
    "from": account.address,
    "to": "0x36334Fc30798F77a880e26850BDCB3D167E91807",
    "value": 1000000000000000,
    "nonce": w3.eth.get_transaction_count(account.address),
    "gas": 200000,
    "maxFeePerGas": 2000000000,
    "maxPriorityFeePerGas": 1000000000,
}

signedTX = w3.eth.account.sign_transaction(transaction, account.key)

tx_hash = w3.eth.send_raw_transaction(signedTX.rawTransaction)
tx = w3.eth.get_transaction(tx_hash)
print(tx)
