import asyncio
from unittest import result
from solders.pubkey import Pubkey  # type: ignore
from solana.rpc.async_api import AsyncClient
from asyncstdlib import enumerate
from solana.rpc.websocket_api import connect
from solders.rpc.config import RpcTransactionLogsFilterMentions  # type: ignore
from conf import config, logger


class RaydiumNewPools:
    """
    `RaydiumNewPools` events listener

    """

    BASE_WSS_ENDPOINT = "wss://api.mainnet-beta.solana.com"
    RAYDIUM_AUTHORITY = Pubkey.from_string(
        "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1"
    )
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
                commitment="finalized",
            )
            logger.info("STARTED EVENT!!")
            while True:
                data = await websocket.recv()
                _result = data[0].result
                if hasattr(_result, "value"):
                    result = _result.value
                    log_signature, logs = result.signature, result.logs
                    if any("Program log: initialize2:" in log for log in logs):
                        print(log_signature)
                else:
                    logger.warning(_result)

    async def start(self):
        """Run bot"""
        _is_missing_key = [key for key in self.ENV_ATTR if key not in config]
        if _is_missing_key:
            msg = f"Set the following {len(_is_missing_key)} key(s) in the .env file: {', '.join(_is_missing_key)}"
            logger.info(msg)
            exit()
        # setup our private node
        await self.setup_private_client()
        await self.subscribe_to_log()


if __name__ == "__main__":
    asyncio.run(RaydiumNewPools().start())
