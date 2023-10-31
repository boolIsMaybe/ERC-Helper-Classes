import sqlite3
from dotenv import load_dotenv
from os import getenv
import json


from web3 import Web3  # // Link to docs: https://shorturl.at/agMQX // #
from eth_typing import (  # // Link to docs: https://shorturl.at/cBJ28 // #
    ChecksumAddress,
    TypeStr,
)

load_dotenv(".env")

APISTRING: str = getenv("INFURA_API_KEY")  # type: ignore

w3: Web3 = Web3(Web3.HTTPProvider(APISTRING))

UNIFACTORYADDRESS: ChecksumAddress = Web3.to_checksum_address(
    "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"
)

with open(getenv("PATH_TO_UNI_FACT_ABI")) as uniFact_abi:  # type: ignore
    UNIFACTABI: TypeStr = json.load(uniFact_abi)

with open(getenv("PATH_TO_UNI_LP_ABI")) as uniLP_abi:  # type: ignore
    UNILPABI: TypeStr = json.load(uniLP_abi)

uniswapFactory = w3.eth.contract(
    address=UNIFACTORYADDRESS,
    abi=UNIFACTABI,
)


class ContextManager:
    def __init__(self):
        self.dbName = "database/pools.db"

    def __enter__(self):
        self.conn = sqlite3.connect(self.dbName)
        return self.conn

    def __exit__(self, exc_type, exc_value, traceback):
        self.conn.close()


def updateUNIv2Pairs():
    allPairs = uniswapFactory.functions.allPairsLength().call()

    with ContextManager() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM pools")
        count = cursor.fetchone()[0]
        print(
            f"There is {count} pools in the database already\n scanning pools in range {count}-{allPairs}"
        )

    # Iterate through all the liquidity pool pairs
    for pool in range(count, allPairs):
        print(f"Scanning Pool #{pool}")
        loopedPairAddress = uniswapFactory.functions.allPairs(pool).call()
        loopedPairContract = w3.eth.contract(address=loopedPairAddress, abi=UNILPABI)
        token0 = loopedPairContract.functions.token0().call()
        token1 = loopedPairContract.functions.token1().call()

        addPoolToDatabase(address=loopedPairAddress, token0=token0, token1=token1)


def buildDatabase():
    with ContextManager() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS pools (address TEXT,token0 TEXT,token1 TEXT)"
        )
        conn.commit()


def addPoolToDatabase(address, token0, token1):
    with ContextManager() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            INSERT INTO pools (address, token0, token1)
            VALUES ('{address}', '{token0}', '{token1}')
            """
        )
        conn.commit()
        print(
            f"""
Pool added to Database:\n
    Pool Address: {address}\n
    Token0: {token0}\n
    Token1: {token1}\n
            """
        )


def retrieveDBSize():
    with ContextManager() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM pools")
        count = cursor.fetchone()[0]
        print(f"There is {count} pools in the database")
        return count


updateUNIv2Pairs()
