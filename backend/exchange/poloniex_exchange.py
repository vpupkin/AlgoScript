import aiohttp
import asyncio
import hmac
import hashlib
import time
import json
from typing import List, Dict, Optional, Any
from decimal import Decimal
from datetime import datetime
from .base_exchange import BaseExchange, MarketDataReal, OrderResponseReal, BalanceReal
import logging

logger = logging.getLogger(__name__)

class PoloniexExchange(BaseExchange):
    """Poloniex cryptocurrency exchange implementation"""
    
    def __init__(self, api_key: str, api_secret: str, config: Dict[str, Any] = None):
        super().__init__(api_key, api_secret, config)
        self.base_url = "https://api.poloniex.com"
        self.session: Optional[aiohttp.ClientSession] = None
        self._rate_limiter = asyncio.Semaphore(30)  # 30 requests per minute for private endpoints
    
    def get_exchange_name(self) -> str:
        return "poloniex"
    
    async def connect(self) -> bool:
        """Establish connection to Poloniex"""
        try:
            connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={"User-Agent": "AlgoScript/1.0"}
            )
            
            # Test connection with a simple API call
            await self.get_ticker_data("BTC_USDT")
            self._connected = True
            logger.info("Connected to Poloniex exchange")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Poloniex: {str(e)}")
            return False
    
    async def disconnect(self) -> None:
        """Close Poloniex connection"""
        if self.session and not self.session.closed:
            await self.session.close()
            self._connected = False
            logger.info("Disconnected from Poloniex exchange")
    
    def _generate_signature(self, timestamp: str, method: str, path: str, body: str = "") -> str:
        """Generate HMAC-SHA256 signature for authenticated requests"""
        message = timestamp + method + path + body
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _get_auth_headers(self, method: str, path: str, body: str = "") -> Dict[str, str]:
        """Generate authentication headers for API requests"""
        timestamp = str(int(time.time() * 1000))
        signature = self._generate_signature(timestamp, method, path, body)
        
        return {
            "PF-API-KEY": self.api_key,
            "PF-API-SIGN": signature,
            "PF-API-TIMESTAMP": timestamp,
            "Content-Type": "application/json"
        }
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        authenticated: bool = False
    ) -> Dict[str, Any]:
        """Make API request with rate limiting and error handling"""
        if not self.session:
            raise ConnectionError("Exchange not connected")
        
        async with self._rate_limiter:
            url = f"{self.base_url}{endpoint}"
            headers = {}
            json_data = None
            
            if authenticated:
                body = ""
                if data:
                    json_data = data
                    body = json.dumps(data)
                headers.update(self._get_auth_headers(method, endpoint, body))
            
            try:
                async with self.session.request(
                    method, url, params=params, json=json_data, headers=headers
                ) as response:
                    if response.status == 429:
                        # Rate limit exceeded
                        retry_after = int(response.headers.get('Retry-After', '60'))
                        logger.warning(f"Rate limit exceeded, waiting {retry_after} seconds")
                        await asyncio.sleep(retry_after)
                        return await self._make_request(method, endpoint, params, data, authenticated)
                    
                    response.raise_for_status()
                    return await response.json()
                    
            except aiohttp.ClientError as e:
                logger.error(f"Request failed: {method} {url} - {str(e)}")
                raise ConnectionError(f"API request failed: {str(e)}")
    
    async def get_ticker_data(self, symbol: str) -> MarketDataReal:
        """Get current ticker data for a specific trading pair"""
        endpoint = "/public"
        params = {"command": "returnTicker"}
        
        response = await self._make_request("GET", endpoint, params=params)
        
        if symbol not in response:
            raise ValueError(f"Symbol {symbol} not found")
        
        ticker = response[symbol]
        return MarketDataReal(
            symbol=symbol,
            timestamp=datetime.utcnow(),
            price=Decimal(ticker.get('last', '0')),
            bid=Decimal(ticker.get('highestBid', '0')),
            ask=Decimal(ticker.get('lowestAsk', '0')),
            volume=Decimal(ticker.get('baseVolume', '0')),
            high_24h=Decimal(ticker.get('high24hr', '0')),
            low_24h=Decimal(ticker.get('low24hr', '0')),
            change_24h=Decimal(ticker.get('percentChange', '0'))
        )
    
    async def get_all_tickers(self) -> Dict[str, MarketDataReal]:
        """Get ticker data for all available trading pairs"""
        endpoint = "/public"
        params = {"command": "returnTicker"}
        
        response = await self._make_request("GET", endpoint, params=params)
        
        tickers = {}
        for symbol, ticker in response.items():
            tickers[symbol] = MarketDataReal(
                symbol=symbol,
                timestamp=datetime.utcnow(),
                price=Decimal(ticker.get('last', '0')),
                bid=Decimal(ticker.get('highestBid', '0')),
                ask=Decimal(ticker.get('lowestAsk', '0')),
                volume=Decimal(ticker.get('baseVolume', '0')),
                high_24h=Decimal(ticker.get('high24hr', '0')),
                low_24h=Decimal(ticker.get('low24hr', '0')),
                change_24h=Decimal(ticker.get('percentChange', '0'))
            )
        
        return tickers
    
    async def place_market_order(
        self, 
        symbol: str, 
        side: str, 
        quantity: Decimal
    ) -> OrderResponseReal:
        """Place a market order"""
        endpoint = "/tradingApi"
        
        # For market orders, we need to get current price and place a limit order close to market
        ticker = await self.get_ticker_data(symbol)
        
        if side.upper() == "BUY":
            # Buy at ask price (or slightly above for market execution)
            price = ticker.ask * Decimal("1.001")  # 0.1% above ask
        else:
            # Sell at bid price (or slightly below for market execution)
            price = ticker.bid * Decimal("0.999")  # 0.1% below bid
        
        order_data = {
            "command": "buy" if side.upper() == "BUY" else "sell",
            "currencyPair": symbol,
            "rate": str(price),
            "amount": str(quantity)
        }
        
        response = await self._make_request("POST", endpoint, data=order_data, authenticated=True)
        
        return OrderResponseReal(
            order_id=response.get("orderNumber", ""),
            symbol=symbol,
            side=side.upper(),
            quantity=quantity,
            price=price,
            status="PENDING",
            timestamp=datetime.utcnow(),
            fees=Decimal("0")
        )
    
    async def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        price: Decimal
    ) -> OrderResponseReal:
        """Place a limit order"""
        endpoint = "/tradingApi"
        
        order_data = {
            "command": "buy" if side.upper() == "BUY" else "sell",
            "currencyPair": symbol,
            "rate": str(price),
            "amount": str(quantity)
        }
        
        response = await self._make_request("POST", endpoint, data=order_data, authenticated=True)
        
        return OrderResponseReal(
            order_id=response.get("orderNumber", ""),
            symbol=symbol,
            side=side.upper(),
            quantity=quantity,
            price=price,
            status="PENDING",
            timestamp=datetime.utcnow(),
            fees=Decimal("0")
        )
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an existing order"""
        endpoint = "/tradingApi"
        
        cancel_data = {
            "command": "cancelOrder",
            "orderNumber": order_id
        }
        
        try:
            response = await self._make_request("POST", endpoint, data=cancel_data, authenticated=True)
            return response.get("success", 0) == 1
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {str(e)}")
            return False
    
    async def get_account_balances(self) -> List[BalanceReal]:
        """Get current account balances"""
        endpoint = "/tradingApi"
        
        balance_data = {
            "command": "returnBalances"
        }
        
        response = await self._make_request("POST", endpoint, data=balance_data, authenticated=True)
        
        balances = []
        for currency, amount in response.items():
            if Decimal(amount) > 0:
                balances.append(BalanceReal(
                    currency=currency,
                    available=Decimal(amount),
                    locked=Decimal("0")  # Poloniex doesn't separate locked balances in this endpoint
                ))
        
        return balances
    
    async def get_order_status(self, order_id: str) -> Optional[str]:
        """Get the status of an order"""
        endpoint = "/tradingApi"
        
        # Check open orders first
        open_orders_data = {
            "command": "returnOpenOrders",
            "currencyPair": "all"
        }
        
        try:
            response = await self._make_request("POST", endpoint, data=open_orders_data, authenticated=True)
            
            # Search through all currency pairs
            for pair_orders in response.values():
                if isinstance(pair_orders, list):
                    for order in pair_orders:
                        if order.get("orderNumber") == order_id:
                            return "OPEN"
            
            # If not in open orders, check trade history for filled orders
            trade_history_data = {
                "command": "returnTradeHistory",
                "currencyPair": "all",
                "limit": 100
            }
            
            history_response = await self._make_request("POST", endpoint, data=trade_history_data, authenticated=True)
            
            for pair_trades in history_response.values():
                if isinstance(pair_trades, list):
                    for trade in pair_trades:
                        if trade.get("orderNumber") == order_id:
                            return "FILLED"
            
            return "CANCELLED"  # Assume cancelled if not found in open or filled
            
        except Exception as e:
            logger.error(f"Failed to get order status for {order_id}: {str(e)}")
            return None