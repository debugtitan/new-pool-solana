import asyncio
from solana.rpc.async_api import AsyncClient
from conf import config, logger


class RaydiumNewPools:
    """
    `RaydiumNewPools` events listener

    """

    BASE_RPC_ENDPOINT = "https://api.mainnet-beta.solana.com"
    ENV_ATTR = ["PRIVATE_CLIENT", "TELEGRAM_CHANNEL", "TELEGRAM_BOT_TOKEN"]

    def __init__(self):
        self.client: AsyncClient = None
        self.private_client: AsyncClient = None

    async def setup_client(self):
        """setup client connection"""
        self.client = AsyncClient(self.BASE_RPC_ENDPOINT)

    async def setup_private_client(self):
        """setup a private rpc client endpoint"""
        self.private_client = AsyncClient(config["PRIVATE_CLIENT"])

    async def start(self):
        """Run bot"""
        await self.setup_client()
        successful_connection = await self.client.is_connected()

        if successful_connection == False:
            logger.error("check your rpc node")
            exit()

        _is_missing_key = [key for key in self.ENV_ATTR if key not in config]
        if _is_missing_key:
            msg = f"Set the following {len(_is_missing_key)} key(s) in the .env file: {', '.join(_is_missing_key)}"
            logger.info(msg)
            exit()
        # setup our private node
        await self.setup_private_client()
        



if __name__ == "__main__":
    asyncio.run(RaydiumNewPools().start())
