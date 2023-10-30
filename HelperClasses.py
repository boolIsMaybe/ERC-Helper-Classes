import json
from dotenv import load_dotenv
from os import getenv
from decimal import Decimal

from web3 import Web3
from eth_typing import ChecksumAddress, TypeStr

# Load environment variables from a .env file
load_dotenv(".env")

# Initialize generic ERC20 ABI
with open(getenv("PATH_TO_ERC_ABI"), "r") as abi_json:  # type: ignore
    ERC20ABI: TypeStr = json.load(abi_json)

# Initialize Uniswap Factory ABI
with open(getenv("PATH_TO_UNI_FACT_ABI")) as uniFact_abi:  # type: ignore
    UNIFACTABI: TypeStr = json.load(uniFact_abi)

# Initialize Uniswap Router ABI
with open(getenv("PATH_TO_UNI_ROUTER_ABI")) as uniRout_abi:  # type: ignore
    UNIROUTERABI: TypeStr = json.load(uniRout_abi)

# Initialize Generic Uniswap LP ABI
with open(getenv("PATH_TO_UNI_LP_ABI")) as uniLP_abi:  # type: ignore
    UNILPABI: TypeStr = json.load(uniLP_abi)

# Initialize Uniswap Router Address
UNIROUTERADDRESS: ChecksumAddress = Web3.to_checksum_address(
    "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
)

# Initialize Uniswap Factory Address
UNIFACTORYADDRESS: ChecksumAddress = Web3.to_checksum_address(
    "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"
)

# Initialize WETH Address
WETHADDRESS: ChecksumAddress = Web3.to_checksum_address(
    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
)

APISTRING: str = getenv("INFURA_API_KEY")  # type: ignore


class Erc20Token:
    def __init__(
        self, address: str, pairTokenAddress: str | ChecksumAddress = WETHADDRESS
    ):
        """
        Initialize an ERC20 token with specified addresses and web3 connection.

        Args:
            address (str): The ERC20 token contract address.
            pairTokenAddress (str): Address of the paired token (default is WETH).

        Attributes:
            w3 (Web3): Web3 instance for connecting to Ethereum.
            address (ChecksumAddress): Checksum format of the ERC20 token address.
            symbol (str): Symbol of the ERC20 token.
            contract (Contract): ERC20 token contract instance.
            decimals (int): Number of decimal places for the token.
            uniswapFactory (Contract): Uniswap Factory contract instance.
            pairTokenAddress (ChecksumAddress): Checksum format of the paired token address.
            pairContract (Contract): Paired token contract instance.
        """
        # Initialize Web3 connection
        self.w3: Web3 = Web3(Web3.HTTPProvider(APISTRING))
        # Convert and store token address in checksum format
        self.address: ChecksumAddress = Web3.to_checksum_address(address)
        # Initialize Callable Contract Object
        self.contract = self.w3.eth.contract(address=self.address, abi=ERC20ABI)
        # Get the symbol of the token
        self.symbol: str = self.contract.functions.symbol().call()
        # Get the decimal places for the token
        self.decimals: int = self.get_decimals()
        # Initialize callable Factory Contract Object
        self.uniswapFactory = self.w3.eth.contract(
            address=UNIFACTORYADDRESS,
            abi=UNIFACTABI,
        )
        # Convert and store pair token address in checksum format
        self.pairTokenAddress: ChecksumAddress = self.w3.to_checksum_address(
            pairTokenAddress
        )
        # Initialize Callable pair Contract Object
        self.pairContract = self.w3.eth.contract(
            address=self.pairTokenAddress, abi=ERC20ABI
        )

    def get_decimals(self) -> int:
        """
        Get the number of decimal places for the token.

        Returns:
            int: Number of decimal places.
        """
        return self.contract.functions.decimals().call()

    def get_balance(self, address) -> Decimal:
        """
        Get the balance of the token for a specific address.

        Args:
            address (ChecksumAddress): The address to check the balance for.

        Returns:
            Decimal: The balance of the token.
        """
        return (
            Decimal(self.contract.functions.balanceOf(address).call())
            / 10**self.decimals
        )

    def normalizeValue(self, value, decimalAmount: int) -> Decimal:
        """
        Normalize a value given the value of the decimal counter.

        Args:
            value: The value to normalize.
            decimalAmount (int): The number of decimal places for the token.

        Returns:
            Decimal: The normalized value.
        """
        return Decimal(value) / 10**decimalAmount

    def getTopLPAddresses(self) -> list | None:
        """
        Find and return the top 2 liquidity pool addresses with the largest reserves.

        Returns:
            list | None: List of the top 2 liquidity pool addresses or None if none are found.
        """
        # Retrieve the amount of created pairs
        allPairs: int = self.uniswapFactory.functions.allPairsLength().call()

        # Initialize Lists for object placements
        liquidityPools: list = []
        poolData: list = []

        # Search for pairs
        for pool in range(allPairs):
            loopedPairAddress: ChecksumAddress = self.uniswapFactory.functions.allPairs(
                pool
            ).call()
            loopedPairContract = self.w3.eth.contract(
                address=loopedPairAddress, abi=UNILPABI
            )

            token0: ChecksumAddress = loopedPairContract.functions.token0().call()
            token1: ChecksumAddress = loopedPairContract.functions.token1().call()

            # Check if the pair exists and determine its position in the pool[0 or 1]
            if (token0 == self.address and token1 == self.pairTokenAddress) or (
                token1 == self.address and token0 == self.pairTokenAddress
            ):
                # Get the reserves from the pair contract
                (
                    reserve0,
                    reserve1,
                    _,
                ) = loopedPairContract.functions.getReserves().call()
                if loopedPairContract.functions.token0().call() == self.address:
                    # Normalize the reserves using `normalizeValue()`
                    normalized_reserve0: Decimal = self.normalizeValue(
                        reserve0, self.decimals
                    )
                    normalized_reserve1: Decimal = self.normalizeValue(
                        reserve1, self.pairContract.functions.decimals().call()
                    )

                elif loopedPairContract.functions.token1().call() == self.address:
                    normalized_reserve0: Decimal = self.normalizeValue(
                        reserve1, self.pairContract.functions.decimals().call()
                    )
                    normalized_reserve1: Decimal = self.normalizeValue(
                        reserve0, self.decimals
                    )

                else:
                    # Edge case that an improper LP was provided
                    print(
                        "Error during pool finding, no pairs were found. \n Exiting...."
                    )
                    exit()

                # Append the normalized reserve data to the list
                poolData.append(
                    (loopedPairAddress, normalized_reserve0, normalized_reserve1)
                )

                # Find the top 2 pools and save them to a new list
                sortedPools = sorted(poolData, key=lambda x: x[1] + x[2], reverse=True)
                top2Pools: list = sortedPools[:2]
                liquidityPools = [pool[0] for pool in top2Pools]

                # Return the top 2 pools
                return liquidityPools


class LiquidityPool:
    def __init__(self, address):
        """
        Initialize a LiquidityPool object with a specified address.

        Args:
            address (str): The address of the LiquidityPool contract.

        Attributes:
            w3 (Web3): Web3 instance for connecting to Ethereum.
            address (ChecksumAddress): Checksum format of the LiquidityPool contract address.
            contract (Contract): LiquidityPool contract instance.
            token0 (ChecksumAddress): Address of the first token in the pair.
            token1 (ChecksumAddress): Address of the second token in the pair.
            router (Contract): Uniswap Router contract instance.
        """
        self.w3: Web3 = Web3(Web3.HTTPProvider(APISTRING))
        self.address: ChecksumAddress = Web3.to_checksum_address(address)
        self.contract = self.w3.eth.contract(address=self.address, abi=UNILPABI)
        self.token0: ChecksumAddress = self.contract.functions.token0().call()
        self.token1: ChecksumAddress = self.contract.functions.token1().call()
        self.router = self.contract = self.w3.eth.contract(
            address=UNIROUTERADDRESS, abi=UNIROUTERABI
        )

    def calculateArbTrade(self):
        """
        Calculate an arbitrage trade within the liquidity pool.

        This method should be implemented to calculate arbitrage opportunities.

        Returns:
            The outcome of the arbitrage trade.
        """
        pass


# Define the ArbTransaction class
class ArbTransaction:
    def __init__(
        self,
        lp: LiquidityPool,
        amountIn: int,  # Amount of Input Tokens to Send
        amountOutMin: int,  # Min Amount Received
        path: list,  # List of addresses for the trade route
        receivingAddress: ChecksumAddress,  # Msg.sender
        deadline: int,  # Timestamp of the tx deadline
    ):
        """
        Initialize an arbitrage transaction with specified parameters.

        Args & Attributes:
            lp (LiquidityPool): The LiquidityPool object for the trade.
            amountIn (int): The amount of input tokens to be swapped.
            amountOutMin (int): The minimum amount of output tokens expected.
            path (list): A list of token addresses that represent the swap route.
            receivingAddress (str): The recipient address for the output tokens.
            deadline (int): The deadline by which the transaction must be executed.

        """
        self.lp = lp
        self.amountIn = amountIn
        self.amountOutMin = amountOutMin
        self.path = path
        self.receivingAddress = receivingAddress
        self.deadline = deadline

    def executeTransaction(self):
        """
        Execute a token swap transaction using the provided parameters.

        Returns:
        The outcome of the trade, including the input tokens sent and
        the output tokens received.
        """
        return lp.contract.functions.swapExactTokensForTokens(
            self.amountIn,
            self.amountOutMin,
            self.path,
            self.receivingAddress,
            self.deadline,
        ).call()


##@//-----------------\\@##
##@//-----------------\\@##
##!@//-Testing Code Below-\\@##
##@//-----------------\\@##
##@//-----------------\\@##

# . Chain Link contract as a test
CHAINLINKADDRESS = "0x514910771AF9Ca656af840dff83E8264EcF986CA"
test = Erc20Token(address=CHAINLINKADDRESS)

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
