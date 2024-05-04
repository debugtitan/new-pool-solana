import asyncio
from solana.rpc.async_api import AsyncClient



class RaydiumNewPools:
    """
    `RaydiumNewPools` events listener
    
    """
    BASE_RPC_ENDPOINT= ""

    def __init__(self):
        self.client = self.setup_client()
        self.private_client = self.setup_private_client()

    async def setup_client(self):
        """ setup client connection"""
        return AsyncClient(self.BASE_RPC_ENDPOINT)


    async def setup_private_client(self):
        """ setup a private rpc client endpoint"""