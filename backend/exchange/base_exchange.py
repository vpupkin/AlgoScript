from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel

class MarketDataReal(BaseModel):
    symbol: str
    timestamp: datetime
    price: Decimal
    bid: Decimal
    ask: Decimal
    volume: Decimal
    high_24h: Decimal
    low_24h: Decimal
    change_24h: Decimal

class OrderResponseReal(BaseModel):
    order_id: str
    symbol: str
    side: str  # BUY or SELL
    quantity: Decimal
    price: Decimal
    status: str  # PENDING, FILLED, CANCELLED
    timestamp: datetime
    fees: Decimal = Decimal("0")

class BalanceReal(BaseModel):
    currency: str
    available: Decimal
    locked: Decimal

class BaseExchange(ABC):
    """Abstract base class for all cryptocurrency exchanges"""
    
    def __init__(self, api_key: str, api_secret: str, config: Dict[str, Any] = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.config = config or {}
        self.exchange_name = self.get_exchange_name()
        self._connected = False
    
    @abstractmethod
    def get_exchange_name(self) -> str:
        """Return the exchange name identifier"""
        pass
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to the exchange"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close exchange connection gracefully"""
        pass
    
    @abstractmethod
    async def get_ticker_data(self, symbol: str) -> MarketDataReal:
        """Get current ticker data for a specific trading pair"""
        pass
    
    @abstractmethod
    async def get_all_tickers(self) -> Dict[str, MarketDataReal]:
        """Get ticker data for all available trading pairs"""
        pass
    
    @abstractmethod
    async def place_market_order(
        self, 
        symbol: str, 
        side: str, 
        quantity: Decimal
    ) -> OrderResponseReal:
        """Place a market order"""
        pass
    
    @abstractmethod
    async def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        price: Decimal
    ) -> OrderResponseReal:
        """Place a limit order"""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an existing order"""
        pass
    
    @abstractmethod
    async def get_account_balances(self) -> List[BalanceReal]:
        """Get current account balances"""
        pass
    
    @abstractmethod
    async def get_order_status(self, order_id: str) -> Optional[str]:
        """Get the status of an order"""
        pass
    
    def is_connected(self) -> bool:
        """Check if the exchange is connected"""
        return self._connected
    
    async def validate_symbol(self, symbol: str) -> bool:
        """Validate if a trading symbol exists on the exchange"""
        try:
            await self.get_ticker_data(symbol)
            return True
        except:
            return False