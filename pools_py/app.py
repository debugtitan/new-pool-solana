import asyncio
import time
import requests
from solders.pubkey import Pubkey  # type: ignore
from solders.rpc.config import RpcTransactionLogsFilterMentions  # type: ignore
from solders.signature import Signature  # type: ignore
from solana.rpc.async_api import AsyncClient
from solana.rpc.websocket_api import connect
from websockets.exceptions import ConnectionClosedError
from conf import config, logger
from utils import format_number, unpack_metadata_account, calculate_asset_value

__all__ = ["RayduimNewPools"]


class UiTokenAmount:
    def __init__(self, ui_amount, decimals, amount, ui_amount_string):
        self.ui_amount = ui_amount
        self.decimals = decimals
        self.amount = amount
        self.ui_amount_string = ui_amount_string


class UiTransactionTokenBalance:
    def __init__(self, account_index, mint, ui_token_amount, owner, program_id):
        self.account_index = account_index
        self.mint = mint
        self.ui_token_amount: UiTokenAmount = ui_token_amount
        self.owner = owner
        self.program_id = program_id


class RaydiumNewPools:
    """
    `RaydiumNewPools` events listener
    """

    BASE_WSS_ENDPOINT = "wss://api.mainnet-beta.solana.com"
    RAYDIUM_AUTHORITY = Pubkey.from_string(
        "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1"
    )
    METADATA_PROGRAM_ID = Pubkey.from_string("metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s")
    WRAPPED_SOL = "So11111111111111111111111111111111111111112"
    ENV_ATTR = ["PRIVATE_CLIENT", "TELEGRAM_CHANNEL", "TELEGRAM_BOT_TOKEN"]

    def __init__(self):
        self.client = AsyncClient(self.BASE_WSS_ENDPOINT)
        self.private_client: AsyncClient = None

    async def setup_private_client(self):
        """setup a private rpc client endpoint"""
        self.private_client = AsyncClient(config["PRIVATE_CLIENT"])

    async def subscribe_to_log(self):
        async with connect(self.BASE_WSS_ENDPOINT) as websocket:
            await websocket.logs_subscribe(
                RpcTransactionLogsFilterMentions(self.RAYDIUM_AUTHORITY),
                commitment="processed",
            )
            logger.info("STARTED EVENT!!")
            while True:
                try:
                    data = await websocket.recv()
                    _result = data[0].result
                    if hasattr(_result, "value"):
                        result = _result.value
                        log_signature, logs = result.signature, result.logs
                        if any("Program log: initialize2:" in log for log in logs):
                            print(log_signature)
                    else:
                        logger.warning(_result)
                except ConnectionClosedError as e:
                    logger.error(e)
                    time.sleep(10)

    async def get_parsed_transaction(self, signature):
        txn_signature = Signature.from_string(signature)
        try:
            txn = await self.private_client.get_transaction(
                txn_signature, "json", max_supported_transaction_version=0
            )
            data = txn.value.transaction.meta
            if hasattr(data, "post_token_balances"):
                result = data.post_token_balances
                if len(result) > 1:
                    base_token, quote_token = None, None
                    # certainly we have instructions needed
                    _base_token, _quote_token = result[0], result[1]
                    if _base_token.mint == self.WRAPPED_SOL:
                        quote_token = _base_token
                        base_token = _quote_token
                    else:
                        quote_token = _quote_token
                        base_token = _base_token

                    if base_token and quote_token != None:
                        await self.compile_message(base_token, quote_token)

        except Exception as e:
            logger.warning(f"get_parsed_transaction {e}")

    async def get_token_meta(self, mint):
        """fetch the mint token metadata"""
        program_address = Pubkey.find_program_address(
            [b"metadata", bytes(self.METADATA_PROGRAM_ID), bytes(mint)],
            self.METADATA_PROGRAM_ID,
        )[0]
        meta = await self.private_client.get_account_info_json_parsed(program_address)
        meta_info = await unpack_metadata_account(meta.value.data)
        return meta_info
    
    async def fetch_token_supply(self, mint):
        """ Fetch Token Supply"""
        supply = await self.private_client.get_token_supply(mint)
        return supply.value.ui_amount
    
    async def fetch_token_description_from_uri(self,uri):
        """ Fetch token uri i.e IPFS blockchain data """
        data =  requests.get(uri).json()
        return data['description'] if data['description'] else None

         
    async def compile_message(
        self,
        _base_token: UiTransactionTokenBalance,
        _quote_token: UiTransactionTokenBalance,
    ):
        """compile alert message for token A and token B"""
        base_token = _base_token.mint
        base_token_pool_amount, quote_token_pool_amount = (
            _base_token.ui_token_amount.ui_amount,
            _quote_token.ui_token_amount.ui_amount,
        )
        _token_supply = await self.fetch_token_supply(base_token)
        _token_price = quote_token_pool_amount/base_token_pool_amount #token price in sol
        _token_mcap = base_token_pool_amount * _token_price #mcap in sol
        token_meta = await self.get_token_meta(base_token)
        print(float(_token_price), _token_mcap)
        token_description = ""
        if token_meta['uri']:
            token_info = await self.fetch_token_description_from_uri(token_meta['uri'])
            token_description = token_info if token_info else ""

        token_name = token_meta['name'] if token_meta['name'] else ""
        token_symbol = token_meta['symbol'] if token_meta['symbol'] else ""
        liquidty = calculate_asset_value(int(quote_token_pool_amount))
        token_supply = format_number(_token_supply)
        token_price = calculate_asset_value(_token_price)
        token_mcap = format_number(calculate_asset_value(_token_mcap))
        
        

        msg = f"{token_name} → ({token_symbol})\n\nMeta™\nBase: {format_number(base_token_pool_amount)} {token_name}\nQuote: {format_number(quote_token_pool_amount)} SOL → (${liquidty})\n\n"
        msg += f"Token Mint → {token_supply} {token_name}\nPrice {token_symbol} → (${token_price})\nMarketCap → (${token_mcap})\n\n{token_description}\n\n"
        print(msg)
        

    async def start(self):
        """Run bot"""
        _is_missing_key = [key for key in self.ENV_ATTR if key not in config]
        if _is_missing_key:
            msg = f"Set the following {len(_is_missing_key)} key(s) in the .env file: {', '.join(_is_missing_key)}"
            logger.info(msg)
            exit()
        # setup our private node
        await self.setup_private_client()
        # await self.subscribe_to_log()
        await self.get_parsed_transaction("3zuywBUbFAPAs2Hfe29yAyvXTG8q7zHekL25usfpVzM8UoxYwGg3QV5nDnCPDRH2pSpFhqx19YEJxR5m9BxcDs1N")


if __name__ == "__main__":
    asyncio.run(RaydiumNewPools().start())
