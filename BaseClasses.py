import json
from dotenv import load_dotenv
from os import getenv
from decimal import Decimal

from web3 import Web3  # // Link to docs: https://shorturl.at/agMQX // #
from eth_account import Account  # // Link to docs: https://shorturl.at/sHW39 // #
from eth_account.signers.local import LocalAccount
from eth_typing import (  # // Link to docs: https://shorturl.at/cBJ28 // #
    ChecksumAddress,
    TypeStr,
)


from .utilsETH import ContextManager as PoolDB

# Load environment variables from a .env file
load_dotenv(".env")

# -- Initialize Global Constants
WETHADDRESS: ChecksumAddress = Web3.to_checksum_address(
    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
)
APISTRING: str = getenv("INFURA_API_KEY")  # type: ignore
PRIVATEKEY: str = getenv("PRIVATE_KEY")  # type: ignore
PRIORITYBOOST = 2  # // Sets constant for +increment of Max Priority Fee


class User:
    def __init__(self):
        # Initialize Web 3 Cursor Object
        self.w3: Web3 = Web3(Web3.HTTPProvider(APISTRING))

        # -- Constants
        self.account: LocalAccount = Account.from_key(PRIVATEKEY)
        self.address: ChecksumAddress = self.account.address
        self.nonce: int = self.w3.eth.get_transaction_count(self.address)

        # -- Chain Variables
        self.gasPrice = self.w3.eth.gas_price
        self.maxPriorityFee = self.w3.eth.max_priority_fee
        self.chainID = self.w3.eth.chain_id

    # -- Class Methods
    def buildTX(self):
        pass

    def signTX(self):
        pass


class Uniswap:
    def __init__(self):
        # Initialize Web 3 Cursor Object & User
        self.w3: Web3 = Web3(Web3.HTTPProvider(APISTRING))
        self.user = User()

        # -- ABI's
        with open(getenv("PATH_TO_UNI_LP_ABI")) as uniLP_abi:  # type: ignore
            self.uniLPABI: TypeStr = json.load(uniLP_abi)
        with open(getenv("PATH_TO_UNI_FACT_ABI")) as uniFact_abi:  # type: ignore
            self.uniFactABI: TypeStr = json.load(uniFact_abi)
        with open(getenv("PATH_TO_UNI_ROUTER_ABI")) as uniRout_abi:  # type: ignore
            self.uniRouterABI: TypeStr = json.load(uniRout_abi)

        # -- Constants
        self.routeraddress: ChecksumAddress = Web3.to_checksum_address(
            "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"  # Uniswap Router Address
        )
        self.factoryaddress: ChecksumAddress = Web3.to_checksum_address(
            "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"  # Uniswap Factory Address
        )
        self.poolDatabase: PoolDB = PoolDB()  # Database of Uni V2 pools

        # -- Callable Contract Objects
        self.router = self.w3.eth.contract(
            address=self.routeraddress, abi=self.uniRouterABI
        )
        self.factory = self.w3.eth.contract(
            address=self.factoryaddress,
            abi=self.uniFactABI,
        )

    # -- Class Methods
    def retrievePoolList(self, token0, token1):
        with self.poolDatabase as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
            SELECT address
            FROM pools
            WHERE (token0 = ? AND token1 = ?) OR (token0 = ? AND token1 = ?);
            """,
                (token0, token1, token1, token0),
            )
            results = cursor.fetchall()
        addresses = [result[0] for result in results]
        return addresses

    def retrieveTopPools(self):
        pass

    def executeRouterSwap(
        self, amountIn, amountOutMin, path, receivingAddress, deadline
    ):
        pass


class Erc20Token:
    def __init__(
        self, address: str, pairTokenAddress: str | ChecksumAddress = WETHADDRESS
    ):
        # Initialize Web 3 Cursor Object & User
        self.w3: Web3 = Web3(Web3.HTTPProvider(APISTRING))
        self.user = User()

        # -- ABI's
        with open(getenv("PATH_TO_ERC_ABI")) as ercabi:  # type: ignore
            self.erc20ABI: TypeStr = json.load(ercabi)

        # -- Constant's
        self.address: ChecksumAddress = Web3.to_checksum_address(address)
        self.contract = self.w3.eth.contract(address=self.address, abi=self.erc20ABI)
        self.uniswap = Uniswap()
        self.pairTokenAddress: ChecksumAddress = self.w3.to_checksum_address(
            pairTokenAddress
        )
        self.pairContract = self.w3.eth.contract(
            address=self.pairTokenAddress, abi=self.erc20ABI
        )

        # -- Token Data
        self.symbol: str = self.contract.functions.symbol().call()
        self.decimals: int = self.getDecimals()

    def getDecimals(self) -> int:
        return self.contract.functions.decimals().call()

    def getBalance(self, address: ChecksumAddress | None) -> Decimal:
        if address != None:
            return (
                Decimal(self.contract.functions.balanceOf(address).call())
                / 10**self.decimals
            )
        else:
            return (
                Decimal(self.contract.functions.balanceOf(self.user.address).call())
                / 10**self.decimals
            )

    def normalizeValue(self, denormalizedValue, decimalAmount: int) -> Decimal:
        return Decimal(denormalizedValue) / 10**decimalAmount

    def denormalizeValue(self, normalizedValue, decimalAmount):
        return normalizedValue * (10**decimalAmount)

    # TODO: Needs to be moved to Uniswap class, split between 2 functions
    def getTopLPAddresses(self) -> list:  # DEPRECATED: ITERATION TOO LONG
        allPairs = self.uniswap.factory.functions.allPairsLength().call()
        liquidityPools = []  # Initialize a list for storing the top liquidity pools
        poolData = []  # Initialize a list for storing pool data

        # Iterate through all the liquidity pool pairs
        for pool in range(235000, allPairs):
            print(f"Scanning Pool #{pool}")
            loopedPairAddress = self.uniswap.factory.functions.allPairs(pool).call()
            loopedPairContract = self.w3.eth.contract(
                address=loopedPairAddress, abi=self.uniswap.uniLPABI
            )
            token0 = loopedPairContract.functions.token0().call()
            token1 = loopedPairContract.functions.token1().call()

            # Check if the current pair is the desired liquidity pool
            if (token0 == self.address and token1 == self.pairTokenAddress) or (
                token1 == self.address and token0 == self.pairTokenAddress
            ):
                print("Liquidity Pool Found!")
                (
                    reserve0,
                    reserve1,
                    timestamp,
                ) = loopedPairContract.functions.getReserves().call()

                # Find position of target token and pair token
                if loopedPairContract.functions.token0().call() == self.address:
                    normalizedReserve0 = self.normalizeValue(reserve0, self.decimals)
                    normalizedReserve1 = self.normalizeValue(
                        reserve1, self.pairContract.functions.decimals().call()
                    )
                elif loopedPairContract.functions.token1().call() == self.address:
                    normalizedReserve0 = self.normalizeValue(
                        reserve1, self.pairContract.functions.decimals().call()
                    )
                    normalizedReserve1 = self.normalizeValue(reserve0, self.decimals)
                else:
                    # Edge case that an improper LP was provided or None was found
                    print(
                        "Error during pool finding, no pairs were found. \n Exiting...."
                    )
                    exit()

                # Append pool data to the list
                poolData.append(
                    (loopedPairAddress, normalizedReserve0, normalizedReserve1)
                )

        # Find the top 2 pools and save their addresses to a new list
        sortedPools = sorted(poolData, key=lambda x: x[1] + x[2], reverse=True)
        liquidityPools = [pool[0] for pool in sortedPools[:2]]

        return liquidityPools  # Return the top 2 liquidity pool addresses


class LiquidityPool:
    def __init__(self, address):
        # Initialize Web 3 Cursor Object & User
        self.w3: Web3 = Web3(Web3.HTTPProvider(APISTRING))
        self.user = User()

        # -- Constant's
        self.uniswap = Uniswap()
        self.address: ChecksumAddress = Web3.to_checksum_address(address)
        self.user = Account.from_key(PRIVATEKEY)

        # -- Callable Contract Objects
        self.contract = self.w3.eth.contract(
            address=self.address, abi=self.uniswap.uniLPABI
        )
        self.router = self.uniswap.router

        # -- Variables
        self.token0: ChecksumAddress = self.contract.functions.token0().call()
        self.token1: ChecksumAddress = self.contract.functions.token1().call()
        self.reserves: list = self.contract.functions.getReserves().call()[:2]
        self.totalSupply: int = self.contract.functions.getReserves().call()

    def calculateArbTrade(self):
        pass

    def getPath(self):
        pass


# ? Contracts for Testing
PEPEADDRESS = "0x6982508145454Ce325dDbE47a25d4ec3d2311933"
LINKADDRESS = "0x514910771AF9Ca656af840dff83E8264EcF986CA"
USDCADDRESS = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"


# ? Pools for Testing
LINKWETH = "0xa2107FA5B38d9bbd2C461D6EDf11B11A50F6b974"
USDCWETH = "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc"
PEPEWETH = "0xa43fe16908251ee70ef74718545e4fe6c5ccec9f"


# # . Debug calls
test = Erc20Token(address=PEPEADDRESS)
print(test.getBalance(None))
print(test.symbol)
lp = LiquidityPool(LINKWETH)  # type: ignore
print(lp.address)
print(lp.token0)
print(lp.token1)
