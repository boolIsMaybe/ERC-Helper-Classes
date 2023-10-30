from web3 import Web3
import json
from decimal import Decimal

from dotenv import load_dotenv
from os import getenv

load_dotenv(".env")

# . Initialize generic ERC20 ABI
with open(getenv("PATH_TO_ERC_ABI"), "r") as abi_json:  # type: ignore
    ERC20ABI = json.load(abi_json)

# . Initialize Uniswap Factory ABI
with open(getenv("PATH_TO_UNI_FACT_ABI")) as uniFact_abi:  # type: ignore
    UNIFACTABI = json.load(uniFact_abi)

# . Initialize Uniswap Router ABI
with open(getenv("PATH_TO_UNI_ROUTER_ABI")) as uniRout_abi:  # type: ignore
    UNIROUTERABI = json.load(uniRout_abi)

# . Initialize Generic Uniswap LP ABI
with open(getenv("PATH_TO_UNI_LP_ABI")) as uniLP_abi:  # type: ignore
    UNILPABI = json.load(uniLP_abi)

# . Initialize  Uniswap Router Address
UNIROUTERADDRESS = Web3.to_checksum_address(
    "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
)

APISTRING = getenv("INFURA_API_KEY")


# . ERC20 Class, meant to be used for easier normalization and contract calls
class Erc20Token:
    def __init__(self, address):
        self.w3 = Web3(Web3.HTTPProvider(APISTRING)) 
        self.address = Web3.to_checksum_address(address)
        self.symbol = self.contract.functions.symbol().call()

        #? Initialize Callable Contract Object
        self.contract = self.w3.eth.contract(address=self.address, abi=ERC20ABI) 

        self.decimals = self.get_decimals()

        #? Initialize callable Factory Contract Object
        self.uniswapFactory = self.w3.eth.contract(
            address=Web3.to_checksum_address(
                "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"
            ),
            abi=UNIFACTABI,
        )

        self.wethAddress = self.w3.to_checksum_address(
            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
        )

        #? Initlaize Callable Weth Contract Object
        self.wethContract = self.w3.eth.contract(address=self.wethAddress, abi=ERC20ABI)

    #? returns the decimal counter for the token
    def get_decimals(self):
        return self.contract.functions.decimals().call()


    #? returns the balance of a given address
    def get_balance(self, address):
        return Decimal(self.contract.functions.balanceOf(address).call()) / 10**18


    #? Normalizes a value given the value of the decimal counter
    def normalizeValue(self, value, decimalAmount):
        return Decimal(value) / 10**decimalAmount


    #? Sorts through all created pools, returns the 2 pools with the largest reserves
    def getTopLPAddresses(self):
        #? Retrieve the amount of created pairs
        allPairs = self.uniswapFactory.functions.allPairsLength().call()

        #? Initialize Lists for object placements
        liquidityPools = []
        poolData = []

        #? Search WETH pairs for the tokens 
        for pool in range(allPairs):
            pairAddress = self.uniswapFactory.functions.allPairs(pool).call()
            pairContract = self.w3.eth.contract(address=pairAddress, abi=UNILPABI)

            token0 = pairContract.functions.token0().call()
            token1 = pairContract.functions.token1().call()

            #? Check if the pair includes the token and WETH
            if (token0 == self.address and token1 == self.wethAddress) or (
                token1 == self.address and token0 == self.wethAddress
            ):
                #? Get the reserves from the pair contract
                reserve0, reserve1, _ = pairContract.functions.getReserves().call()
                if pairContract.functions.token0().call() == self.address:

                    #? Normalize the reserves using `normalizeValue()`
                    normalized_reserve0 = self.normalizeValue(reserve0, self.decimals)
                    normalized_reserve1 = self.normalizeValue(
                        reserve1, self.wethContract.functions.decimals().call()
                    )

                elif pairContract.functions.token1().call() == self.address:
                    normalized_reserve0 = self.normalizeValue(
                        reserve1, self.wethContract.functions.decimals().call()
                    )
                    normalized_reserve1 = self.normalizeValue(reserve0, self.decimals)

                else:
                    #? Edge case that an inproper LP was provided
                    print(
                        "Error during pool reserve normalization, pool is not a pair of target token and WETH"
                    )
                    exit()

                #? Append the normalized reserve data to the list
                poolData.append((pairAddress, normalized_reserve0, normalized_reserve1))

                #? Find the top 2 pools and save them to a new list 
                sortedPools = sorted(poolData, key=lambda x: x[1] + x[2], reverse=True)
                top2Pools = sortedPools[:2]
                liquidityPools = [pool[0] for pool in top2Pools]

                #? Return the top 2 pools
                return liquidityPools


class LiquidityPool:
    def __init__(self, address):
        self.w3 = Web3(Web3.HTTPProvider(APISTRING))
        self.address = Web3.to_checksum_address(address)
        self.contract = self.w3.eth.contract(address=self.address, abi=UNILPABI)

        self.token0 = self.contract.functions.token0().call()
        self.token1 = self.contract.functions.token1().call()
        self.router = self.contract = self.w3.eth.contract(
            address=UNIROUTERADDRESS, abi=UNIROUTERABI
        )

##@//-----------------\\@##
##@//-----------------\\@##
##!@//-Testing Code Below-\\@##
##@//-----------------\\@##
##@//-----------------\\@##

# . Chain Link contract as a test
test = Erc20Token(
    address="0x514910771AF9Ca656af840dff83E8264EcF986CA",
)

# . Debug calls 
print(test.get_balance("0x98FD04890B3c6299b6E262878ED86A264a06feC9"))
print(test.symbol)
lpList = test.getTopLPAddresses()
print(lpList)
poolObjects = []
lp = LiquidityPool(lpList[0])  # type: ignore
print(lp.address)
print(lp.token0)
print(lp.token1)
