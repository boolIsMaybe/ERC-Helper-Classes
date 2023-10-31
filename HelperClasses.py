import json
from dotenv import load_dotenv
from os import getenv
from decimal import Decimal
from utilsETH import ContextManager as PoolDB


from web3 import Web3  # // Link to docs: https://shorturl.at/agMQX // #
from eth_typing import (  # // Link to docs: https://shorturl.at/cBJ28 // #
    ChecksumAddress,
    TypeStr,
)

# Load environment variables from a .env file
load_dotenv(".env")

# Initialize WETH Address
WETHADDRESS: ChecksumAddress = Web3.to_checksum_address(
    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
)

APISTRING: str = getenv("INFURA_API_KEY")  # type: ignore


class Uniswap:
    def __init__(self):
        # Initialize Web 3 Cursor Object
        self.w3: Web3 = Web3(Web3.HTTPProvider(APISTRING))

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
        self.poolDatabase: PoolDB = PoolDB()

        # -- Callable Contract Objects
        self.router = self.w3.eth.contract(
            address=self.routeraddress, abi=self.uniRouterABI
        )
        self.factory = self.w3.eth.contract(
            address=self.factoryaddress,
            abi=self.uniFactABI,
        )

    # -- Uniswap Methods
    def retrievePoolList(self, token0, token1):
        pass


class Erc20Token:
    def __init__(
        self, address: str, pairTokenAddress: str | ChecksumAddress = WETHADDRESS
    ):
        # Initialize Web3 connection
        self.w3: Web3 = Web3(Web3.HTTPProvider(APISTRING))

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
        self.decimals: int = self.get_decimals()

    def get_decimals(self) -> int:
        return self.contract.functions.decimals().call()

    def get_balance(self, address) -> Decimal:
        return (
            Decimal(self.contract.functions.balanceOf(address).call())
            / 10**self.decimals
        )

    def normalizeValue(self, denormalizedValue, decimalAmount: int) -> Decimal:
        return Decimal(denormalizedValue) / 10**decimalAmount

    def denormalizeValue(self, normalizedValue, decimalAmount):
        return normalizedValue * (10**decimalAmount)

    # TODO: Needs to be moved to Uniswap class, and scan the pool DB instead of calling contracts
    # def getTopLPAddresses(self) -> list:  # DEPRECATED: ITERATION TOO LONG
    #     allPairs = self.uniswap.factory.functions.allPairsLength().call()
    #     liquidityPools = []  # Initialize a list for storing the top liquidity pools
    #     poolData = []  # Initialize a list for storing pool data

    #     # Iterate through all the liquidity pool pairs
    #     for pool in range(235000, allPairs):
    #         print(f"Scanning Pool #{pool}")
    #         loopedPairAddress = self.uniswap.factory.functions.allPairs(pool).call()
    #         loopedPairContract = self.w3.eth.contract(
    #             address=loopedPairAddress, abi=self.uniswap.uniLPABI
    #         )
    #         token0 = loopedPairContract.functions.token0().call()
    #         token1 = loopedPairContract.functions.token1().call()

    #         # Check if the current pair is the desired liquidity pool
    #         if (token0 == self.address and token1 == self.pairTokenAddress) or (
    #             token1 == self.address and token0 == self.pairTokenAddress
    #         ):
    #             print("Liquidity Pool Found!")
    #             (
    #                 reserve0,
    #                 reserve1,
    #                 _,
    #             ) = loopedPairContract.functions.getReserves().call()

    #             if loopedPairContract.functions.token0().call() == self.address:
    #                 normalizedReserve0 = self.normalizeValue(reserve0, self.decimals)
    #                 normalizedReserve1 = self.normalizeValue(
    #                     reserve1, self.pairContract.functions.decimals().call()
    #                 )
    #             elif loopedPairContract.functions.token1().call() == self.address:
    #                 normalizedReserve0 = self.normalizeValue(
    #                     reserve1, self.pairContract.functions.decimals().call()
    #                 )
    #                 normalizedReserve1 = self.normalizeValue(reserve0, self.decimals)
    #             else:
    #                 # Edge case that an improper LP was provided or None was found
    #                 print(
    #                     "Error during pool finding, no pairs were found. \n Exiting...."
    #                 )
    #                 exit()

    #             # Append pool data to the list
    #             poolData.append(
    #                 (loopedPairAddress, normalizedReserve0, normalizedReserve1)
    #             )

    #     # Find the top 2 pools and save their addresses to a new list
    #     sortedPools = sorted(poolData, key=lambda x: x[1] + x[2], reverse=True)
    #     liquidityPools = [pool[0] for pool in sortedPools[:2]]

    #     return liquidityPools  # Return the top 2 liquidity pool addresses


class LiquidityPool:
    def __init__(self, address):
        """
        #TODO: Add getReserves function or self.reserves attribute
        """

        self.w3: Web3 = Web3(Web3.HTTPProvider(APISTRING))
        self.uniswap = Uniswap()
        self.address: ChecksumAddress = Web3.to_checksum_address(address)
        self.contract = self.w3.eth.contract(
            address=self.address, abi=self.uniswap.uniLPABI
        )
        self.token0: ChecksumAddress = self.contract.functions.token0().call()
        self.token1: ChecksumAddress = self.contract.functions.token1().call()
        self.router = self.uniswap.router

    def calculateArbTrade(self):
        pass


# Define the RouterTransaction class
class RouterTransaction:
    def __init__(
        self,
        uniswap: Uniswap,
        amountIn: int,  # Amount of Input Tokens to Send
        amountOutMin: int,  # Min Amount Received
        path: list,  # List of addresses for the trade route
        receivingAddress: ChecksumAddress,  # Msg.sender
        deadline: int,  # Timestamp of the tx deadline
    ):
        """
        #TODO: Add checks for more transaction security & gas estimation + fee ratios
        """
        self.uniswap = Uniswap()
        self.amountIn = amountIn
        self.amountOutMin = amountOutMin
        self.path = path
        self.receivingAddress = receivingAddress
        self.deadline = deadline

    def executeTransaction(self):
        return self.uniswap.router.functions.swapExactTokensForTokens(
            self.amountIn,
            self.amountOutMin,
            self.path,
            self.receivingAddress,
            self.deadline,
        ).call()


##//-----------------------------\\##
##//-----------------------------\\##
##! //-Testing Instructions Below-\\ !##
##//-----------------------------\\##
##//-----------------------------\\##

# ? Contracts for Testing
PEPEADDRESS = "0x6982508145454Ce325dDbE47a25d4ec3d2311933"
LINKADDRESS = "0x514910771AF9Ca656af840dff83E8264EcF986CA"
USDCADDRESS = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"


# ? Pools for Testing
LINKWETH = "0xa2107FA5B38d9bbd2C461D6EDf11B11A50F6b974"
USDCWETH = "0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc"
PEPEWETH = "0xa43fe16908251ee70ef74718545e4fe6c5ccec9f"

# ? Create a Token Object By passing an address
token = Erc20Token(USDCADDRESS)

# ? You can then call getTopLPs for the largest liquidity LP's
# // token.getTopLPAddresses() #Scans 270,000 transactions

# ? To save time you can use one of the pool addresses to initialize an LP object
usdclp = LiquidityPool(USDCWETH)

# ? From there we can gather info on the LP and then execute trades


# # . Debug calls
test = Erc20Token(address=PEPEADDRESS)
print(test.get_balance("0x98FD04890B3c6299b6E262878ED86A264a06feC9"))
print(test.symbol)
lp = LiquidityPool(LINKWETH)  # type: ignore
print(lp.address)
print(lp.token0)
print(lp.token1)
