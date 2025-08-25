from typing import Dict, List, Optional, Any
from .base_exchange import BaseExchange, MarketDataReal, OrderResponseReal, BalanceReal
from .poloniex_exchange import PoloniexExchange
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class ExchangeManager:
    """Manages multiple cryptocurrency exchanges for AlgoScript platform"""
    
    def __init__(self):
        self.exchanges: Dict[str, BaseExchange] = {}
        self.active_exchanges: set = set()
        self.default_exchange: Optional[str] = None
    
    async def add_exchange(
        self, 
        exchange_name: str, 
        api_key: str, 
        api_secret: str, 
        config: Dict[str, Any] = None,
        set_as_default: bool = False
    ) -> bool:
        """Add and connect to a cryptocurrency exchange"""
        try:
            exchange = self._create_exchange(exchange_name, api_key, api_secret, config)
            
            if await exchange.connect():
                self.exchanges[exchange_name] = exchange
                self.active_exchanges.add(exchange_name)
                
                if set_as_default or not self.default_exchange:
                    self.default_exchange = exchange_name
                
                logger.info(f"Successfully added {exchange_name} exchange")
                return True
            else:
                logger.error(f"Failed to connect to {exchange_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding {exchange_name} exchange: {str(e)}")
            return False
    
    def _create_exchange(
        self, 
        exchange_name: str, 
        api_key: str, 
        api_secret: str, 
        config: Dict[str, Any] = None
    ) -> BaseExchange:
        """Factory method to create exchange instances"""
        exchange_classes = {
            'poloniex': PoloniexExchange,
            # Future exchanges can be added here:
            # 'binance': BinanceExchange,
            # 'coinbase': CoinbaseExchange,
            # 'kraken': KrakenExchange,
        }
        
        if exchange_name.lower() not in exchange_classes:
            raise ValueError(f"Unsupported exchange: {exchange_name}")
        
        exchange_class = exchange_classes[exchange_name.lower()]
        return exchange_class(api_key, api_secret, config or {})
    
    def get_exchange(self, exchange_name: Optional[str] = None) -> Optional[BaseExchange]:
        """Get exchange instance by name, or default exchange if no name provided"""
        if exchange_name:
            return self.exchanges.get(exchange_name)
        elif self.default_exchange:
            return self.exchanges.get(self.default_exchange)
        return None
    
    async def get_market_data(
        self, 
        symbol: str, 
        exchange_name: Optional[str] = None
    ) -> Optional[MarketDataReal]:
        """Get market data for a symbol from specified exchange or default"""
        exchange = self.get_exchange(exchange_name)
        if not exchange:
            logger.error(f"Exchange not available: {exchange_name or 'default'}")
            return None
        
        try:
            return await exchange.get_ticker_data(symbol)
        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {str(e)}")
            return None
    
    async def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        exchange_name: Optional[str] = None
    ) -> Optional[OrderResponseReal]:
        """Place a market order on specified exchange or default"""
        exchange = self.get_exchange(exchange_name)
        if not exchange:
            logger.error(f"Exchange not available: {exchange_name or 'default'}")
            return None
        
        try:
            return await exchange.place_market_order(symbol, side, quantity)
        except Exception as e:
            logger.error(f"Error placing market order: {str(e)}")
            return None
    
    async def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        price: Decimal,
        exchange_name: Optional[str] = None
    ) -> Optional[OrderResponseReal]:
        """Place a limit order on specified exchange or default"""
        exchange = self.get_exchange(exchange_name)
        if not exchange:
            logger.error(f"Exchange not available: {exchange_name or 'default'}")
            return None
        
        try:
            return await exchange.place_limit_order(symbol, side, quantity, price)
        except Exception as e:
            logger.error(f"Error placing limit order: {str(e)}")
            return None
    
    async def cancel_order(
        self,
        order_id: str,
        exchange_name: Optional[str] = None
    ) -> bool:
        """Cancel an order on specified exchange or default"""
        exchange = self.get_exchange(exchange_name)
        if not exchange:
            logger.error(f"Exchange not available: {exchange_name or 'default'}")
            return False
        
        try:
            return await exchange.cancel_order(order_id)
        except Exception as e:
            logger.error(f"Error cancelling order: {str(e)}")
            return False
    
    async def get_account_balances(
        self,
        exchange_name: Optional[str] = None
    ) -> List[BalanceReal]:
        """Get account balances from specified exchange or default"""
        exchange = self.get_exchange(exchange_name)
        if not exchange:
            logger.error(f"Exchange not available: {exchange_name or 'default'}")
            return []
        
        try:
            return await exchange.get_account_balances()
        except Exception as e:
            logger.error(f"Error getting account balances: {str(e)}")
            return []
    
    async def get_best_price(
        self,
        symbol: str,
        side: str  # BUY or SELL
    ) -> Optional[tuple[Decimal, str]]:
        """Find the best price across all connected exchanges"""
        best_price = None
        best_exchange = None
        
        for exchange_name in self.active_exchanges:
            try:
                exchange = self.exchanges[exchange_name]
                market_data = await exchange.get_ticker_data(symbol)
                
                price = market_data.ask if side.upper() == 'BUY' else market_data.bid
                
                if best_price is None or (
                    side.upper() == 'BUY' and price < best_price
                ) or (
                    side.upper() == 'SELL' and price > best_price
                ):
                    best_price = price
                    best_exchange = exchange_name
                    
            except Exception as e:
                logger.warning(f"Error getting price from {exchange_name}: {str(e)}")
        
        return (best_price, best_exchange) if best_price else None
    
    async def get_aggregated_market_data(
        self,
        symbol: str
    ) -> Dict[str, MarketDataReal]:
        """Get market data for a symbol from all connected exchanges"""
        aggregated_data = {}
        
        for exchange_name in self.active_exchanges:
            try:
                exchange = self.exchanges[exchange_name]
                market_data = await exchange.get_ticker_data(symbol)
                aggregated_data[exchange_name] = market_data
            except Exception as e:
                logger.warning(f"Error getting data from {exchange_name}: {str(e)}")
        
        return aggregated_data
    
    def list_exchanges(self) -> List[str]:
        """List all connected exchanges"""
        return list(self.active_exchanges)
    
    def get_exchange_status(self) -> Dict[str, bool]:
        """Get connection status of all exchanges"""
        status = {}
        for name, exchange in self.exchanges.items():
            status[name] = exchange.is_connected()
        return status
    
    async def disconnect_all(self):
        """Disconnect from all exchanges"""
        for exchange_name, exchange in self.exchanges.items():
            try:
                await exchange.disconnect()
                logger.info(f"Disconnected from {exchange_name}")
            except Exception as e:
                logger.error(f"Error disconnecting from {exchange_name}: {str(e)}")
        
        self.exchanges.clear()
        self.active_exchanges.clear()
        self.default_exchange = None

# Global exchange manager instance
exchange_manager = ExchangeManager()

def get_exchange_manager() -> ExchangeManager:
    """Get the global exchange manager instance"""
    return exchange_manager