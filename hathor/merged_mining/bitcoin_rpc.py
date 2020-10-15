from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, cast

from hathor.merged_mining.jsonrpc import Jsonrpc


class IBitcoinRPC(ABC):
    @abstractmethod
    async def get_block_template(self, *, rules: List[str] = ['segwit'], longpoll_id: Optional[str],
                                 capabilities: List[str] = ['coinbasetxn', 'workid', 'coinbase/append', 'longpoll'],
                                 ) -> Dict:
        """ Method for the [GetBlockTemplate call](https://bitcoin.org/en/developer-reference#getblocktemplate).
        """
        raise NotImplementedError

    @abstractmethod
    async def verify_block_proposal(self, block: bytes) -> Optional[str]:
        """ Method for the [GetBlockTemplate call](https://developer.bitcoin.org/reference/rpc/getblocktemplate.html).
        """
        raise NotImplementedError

    @abstractmethod
    async def submit_block(self, block: bytes) -> Optional[str]:
        """ Method for the [SubmitBlock call](https://developer.bitcoin.org/reference/rpc/submitblock.html).
        """
        raise NotImplementedError

    @abstractmethod
    async def validate_address(self, address: str) -> Dict:
        """ Method for the [ValidateAddress call](https://developer.bitcoin.org/reference/rpc/validateaddress.html).
        """
        raise NotImplementedError


class BitcoinRPC(IBitcoinRPC, Jsonrpc):
    """ Class for making calls to Bitcoin's RPC.

    References:

    - https://bitcoin.org/en/developer-reference#remote-procedure-calls-rpcs
    """

    async def get_block_template(self, *, rules: List[str] = ['segwit'], longpoll_id: Optional[str],
                                 capabilities: List[str] = ['coinbasetxn', 'workid', 'coinbase/append', 'longpoll'],
                                 ) -> Dict:
        data: Dict[str, Any] = {'capabilities': capabilities, 'rules': rules}
        if longpoll_id is not None:
            data['longpollid'] = longpoll_id
        res = await self._rpc_request('getblocktemplate', data)
        return cast(Dict[str, Any], res)

    async def verify_block_proposal(self, block: bytes) -> Optional[str]:
        res = await self._rpc_request('getblocktemplate', {'mode': 'proposal', 'data': block.hex()})
        return cast(Optional[str], res)

    async def submit_block(self, block: bytes) -> Optional[str]:
        res = await self._rpc_request('submitblock', block.hex())
        return cast(Optional[str], res)

    async def validate_address(self, address: str) -> Dict:
        res = await self._rpc_request('validateaddress', address)
        return cast(Dict, res)
