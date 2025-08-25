import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from .models import MarketData
import math

class MockMarketData:
    """
    Mock market data generator for testing AlgoScript strategies.
    Generates realistic-looking price data with indicators.
    """
    
    def __init__(self, symbol: str = "ETHUSD", initial_price: float = 2000.0):
        self.symbol = symbol
        self.current_price = initial_price
        self.candles = []
        self.indicators_cache = {}
        
        # Generate initial historical data
        self._generate_historical_data(100)  # 100 candles of history
    
    def _generate_historical_data(self, count: int):
        """Generate historical candle data"""
        base_time = datetime.utcnow() - timedelta(hours=count * 4)  # 4H candles
        
        for i in range(count):
            timestamp = base_time + timedelta(hours=i * 4)
            
            # Generate realistic price movement
            volatility = 0.02  # 2% volatility
            price_change = random.uniform(-volatility, volatility)
            new_price = self.current_price * (1 + price_change)
            
            # Generate OHLC
            high = new_price * (1 + random.uniform(0, 0.01))
            low = new_price * (1 - random.uniform(0, 0.01))
            open_price = self.current_price if i == 0 else self.candles[-1].close
            close_price = new_price
            
            # Ensure OHLC logic
            high = max(high, open_price, close_price)
            low = min(low, open_price, close_price)
            
            volume = random.uniform(1000, 10000)
            
            candle = MarketData(
                symbol=self.symbol,
                timestamp=timestamp,
                open=open_price,
                high=high,
                low=low,
                close=close_price,
                volume=volume
            )
            
            self.candles.append(candle)
            self.current_price = close_price
    
    def get_current_price(self) -> float:
        """Get current market price"""
        return self.current_price
    
    def get_latest_candle(self) -> MarketData:
        """Get the most recent candle"""
        return self.candles[-1] if self.candles else None
    
    def get_candles(self, count: int = 50) -> List[MarketData]:
        """Get recent candles"""
        return self.candles[-count:] if len(self.candles) >= count else self.candles
    
    def generate_new_candle(self) -> MarketData:
        """Generate a new candle (simulate price movement)"""
        if not self.candles:
            self._generate_historical_data(1)
            return self.candles[-1]
        
        last_candle = self.candles[-1]
        new_timestamp = last_candle.timestamp + timedelta(hours=4)
        
        # Generate price movement with some trend
        volatility = 0.015
        trend = random.uniform(-0.005, 0.005)  # Small trend component
        price_change = trend + random.uniform(-volatility, volatility)
        
        new_price = self.current_price * (1 + price_change)
        
        # Generate OHLC
        high = new_price * (1 + random.uniform(0, 0.008))
        low = new_price * (1 - random.uniform(0, 0.008))
        open_price = self.current_price
        close_price = new_price
        
        # Ensure OHLC logic
        high = max(high, open_price, close_price)
        low = min(low, open_price, close_price)
        
        volume = random.uniform(1000, 10000)
        
        candle = MarketData(
            symbol=self.symbol,
            timestamp=new_timestamp,
            open=open_price,
            high=high,
            low=low,
            close=close_price,
            volume=volume
        )
        
        self.candles.append(candle)
        self.current_price = close_price
        
        # Clear indicator cache when new data arrives
        self.indicators_cache.clear()
        
        return candle
    
    def calculate_ema(self, period: int, data: Optional[List[float]] = None) -> float:
        """Calculate Exponential Moving Average"""
        cache_key = f"EMA_{period}"
        
        if cache_key in self.indicators_cache:
            return self.indicators_cache[cache_key]
        
        if data is None:
            data = [candle.close for candle in self.candles]
        
        if len(data) < period:
            return data[-1] if data else 0.0
        
        # Calculate EMA
        multiplier = 2.0 / (period + 1)
        ema = data[0]
        
        for price in data[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        self.indicators_cache[cache_key] = ema
        return ema
    
    def calculate_rsi(self, period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        cache_key = f"RSI_{period}"
        
        if cache_key in self.indicators_cache:
            return self.indicators_cache[cache_key]
        
        if len(self.candles) < period + 1:
            return 50.0  # Neutral RSI
        
        closes = [candle.close for candle in self.candles[-(period + 1):]]
        gains = []
        losses = []
        
        for i in range(1, len(closes)):
            change = closes[i] - closes[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        
        if avg_loss == 0:
            rsi = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100.0 - (100.0 / (1 + rs))
        
        self.indicators_cache[cache_key] = rsi
        return rsi
    
    def calculate_macd(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Dict[str, float]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        cache_key = f"MACD_{fast_period}_{slow_period}_{signal_period}"
        
        if cache_key in self.indicators_cache:
            return self.indicators_cache[cache_key]
        
        closes = [candle.close for candle in self.candles]
        
        if len(closes) < slow_period:
            result = {"macd": 0.0, "signal": 0.0, "histogram": 0.0}
            self.indicators_cache[cache_key] = result
            return result
        
        # Calculate EMAs
        fast_ema = self.calculate_ema(fast_period, closes)
        slow_ema = self.calculate_ema(slow_period, closes)
        
        # MACD line
        macd_line = fast_ema - slow_ema
        
        # Signal line (EMA of MACD line) - simplified calculation
        signal_line = macd_line * 0.7  # Simplified for demo
        
        # Histogram
        histogram = macd_line - signal_line
        
        result = {
            "macd": macd_line,
            "signal": signal_line,
            "histogram": histogram
        }
        
        self.indicators_cache[cache_key] = result
        return result
    
    def get_volume(self) -> float:
        """Get current volume"""
        return self.candles[-1].volume if self.candles else 0.0
    
    def check_price_cross(self, price: float, indicator_value: float, direction: str) -> bool:
        """Check if price crosses an indicator in specified direction"""
        if len(self.candles) < 2:
            return False
        
        current_candle = self.candles[-1]
        previous_candle = self.candles[-2]
        
        if direction.upper() == "UPWARDS":
            # Price was below indicator and now above
            return (previous_candle.close <= indicator_value and 
                   current_candle.close > indicator_value)
        elif direction.upper() == "DOWNWARDS":
            # Price was above indicator and now below
            return (previous_candle.close >= indicator_value and 
                   current_candle.close < indicator_value)
        
        return False
    
    def simulate_price_change(self, percentage: float):
        """Simulate a specific price change for testing"""
        new_price = self.current_price * (1 + percentage / 100.0)
        self.current_price = new_price
        
        # Update the last candle
        if self.candles:
            self.candles[-1].close = new_price
            self.candles[-1].high = max(self.candles[-1].high, new_price)
            self.candles[-1].low = min(self.candles[-1].low, new_price)
        
        # Clear cache
        self.indicators_cache.clear()

# Global market data instance
market_data_instance = MockMarketData()

def get_market_data(symbol: str = "ETHUSD") -> MockMarketData:
    """Get market data instance for symbol"""
    global market_data_instance
    if market_data_instance.symbol != symbol:
        market_data_instance = MockMarketData(symbol)
    return market_data_instance