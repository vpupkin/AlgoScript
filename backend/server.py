from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
from decimal import Decimal

# AlgoScript imports
from algoscript.interpreter import get_interpreter
from algoscript.models import AlgoScriptRequest, ValidationResult, ExecutionResult
from algoscript.market_data import get_market_data
from exchange.exchange_manager import get_exchange_manager

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="AlgoScript Trading Bot Platform with Real Exchange Integration", version="2.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class AlgoScriptExecuteRequest(BaseModel):
    code: str
    initial_balance: Optional[float] = 10000.0
    events: Optional[List[str]] = ["NEW_CANDLE"]
    use_real_exchange: Optional[bool] = False

class ExchangeConfigRequest(BaseModel):
    exchange_name: str
    api_key: str
    api_secret: str
    set_as_default: Optional[bool] = False

class RealOrderRequest(BaseModel):
    symbol: str
    side: str  # BUY or SELL
    quantity: Decimal
    price: Optional[Decimal] = None
    order_type: str = "MARKET"  # MARKET or LIMIT
    exchange_name: Optional[str] = None

class MarketDataResponse(BaseModel):
    symbol: str
    current_price: float
    ema_50: float
    rsi: float
    macd: dict
    volume: float

class RealMarketDataResponse(BaseModel):
    symbol: str
    timestamp: datetime
    price: Decimal
    bid: Decimal
    ask: Decimal
    volume: Decimal
    high_24h: Decimal
    low_24h: Decimal
    change_24h: Decimal
    exchange: str

# Original routes
@api_router.get("/")
async def root():
    return {"message": "AlgoScript Trading Bot Platform API with Real Exchange Integration"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# AlgoScript routes (existing)
@api_router.post("/algoscript/validate", response_model=ValidationResult)
async def validate_algoscript(request: AlgoScriptRequest):
    """Validate AlgoScript code syntax and semantics"""
    try:
        interpreter = get_interpreter()
        result = interpreter.validate(request.code)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")

@api_router.post("/algoscript/execute", response_model=ExecutionResult)
async def execute_algoscript(request: AlgoScriptExecuteRequest):
    """Execute AlgoScript code and return results (simulation or real trading)"""
    try:
        interpreter = get_interpreter()
        
        # Convert to AlgoScriptRequest
        algo_request = AlgoScriptRequest(
            code=request.code,
            initial_balance=request.initial_balance
        )
        
        # Validate first
        validation = interpreter.validate(request.code)
        if not validation.valid:
            raise HTTPException(status_code=400, detail=f"Invalid AlgoScript: {', '.join(validation.errors)}")
        
        # Create executor with real exchange option
        from algoscript.executor import AlgoScriptExecutor
        executor = AlgoScriptExecutor(
            ast=validation.ast,
            initial_balance=request.initial_balance,
            use_real_exchange=request.use_real_exchange
        )
        
        if len(request.events) == 1:
            # Single event execution
            result = executor.execute(request.events[0])
            return result
        else:
            # Multi-event execution - return the last result
            results = []
            for event in request.events:
                result = executor.simulate_event(event)
                results.append(result)
                if not result.success:
                    break
            return results[-1] if results else ExecutionResult(success=False, error="No results")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")

@api_router.post("/algoscript/execute-multi", response_model=List[ExecutionResult])
async def execute_algoscript_multi(request: AlgoScriptExecuteRequest):
    """Execute AlgoScript code with multiple events and return all results"""
    try:
        interpreter = get_interpreter()
        
        # Convert to AlgoScriptRequest
        algo_request = AlgoScriptRequest(
            code=request.code,
            initial_balance=request.initial_balance
        )
        
        # Validate first
        validation = interpreter.validate(request.code)
        if not validation.valid:
            raise HTTPException(status_code=400, detail=f"Invalid AlgoScript: {', '.join(validation.errors)}")
        
        # Create executor with real exchange option
        from algoscript.executor import AlgoScriptExecutor
        executor = AlgoScriptExecutor(
            ast=validation.ast,
            initial_balance=request.initial_balance,
            use_real_exchange=request.use_real_exchange
        )
        
        results = []
        for event in request.events:
            result = executor.simulate_event(event)
            results.append(result)
            if not result.success:
                break
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")

@api_router.get("/algoscript/example")
async def get_example_code():
    """Get example AlgoScript code"""
    interpreter = get_interpreter()
    return {"code": interpreter.get_example_code()}

# Mock market data routes (existing)
@api_router.get("/algoscript/market-data/{symbol}", response_model=MarketDataResponse)
async def get_market_data_api(symbol: str = "ETHUSD"):
    """Get current market data for a symbol (simulation)"""
    try:
        market_data = get_market_data(symbol)
        
        current_price = market_data.get_current_price()
        ema_50 = market_data.calculate_ema(50)
        rsi = market_data.calculate_rsi()
        macd = market_data.calculate_macd()
        volume = market_data.get_volume()
        
        return MarketDataResponse(
            symbol=symbol,
            current_price=current_price,
            ema_50=ema_50,
            rsi=rsi,
            macd=macd,
            volume=volume
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Market data error: {str(e)}")

@api_router.post("/algoscript/market-data/{symbol}/simulate-candle")
async def simulate_new_candle(symbol: str = "ETHUSD"):
    """Simulate a new candle for testing"""
    try:
        market_data = get_market_data(symbol)
        new_candle = market_data.generate_new_candle()
        
        return {
            "message": "New candle generated",
            "candle": {
                "timestamp": new_candle.timestamp,
                "open": new_candle.open,
                "high": new_candle.high,
                "low": new_candle.low,
                "close": new_candle.close,
                "volume": new_candle.volume
            },
            "current_price": market_data.get_current_price()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")

# NEW: Real Exchange Integration Routes
@api_router.post("/exchange/configure")
async def configure_exchange(config: ExchangeConfigRequest):
    """Configure a real cryptocurrency exchange for live trading"""
    try:
        exchange_manager = get_exchange_manager()
        
        success = await exchange_manager.add_exchange(
            exchange_name=config.exchange_name,
            api_key=config.api_key,
            api_secret=config.api_secret,
            set_as_default=config.set_as_default
        )
        
        if success:
            return {
                "success": True,
                "message": f"Successfully configured {config.exchange_name} exchange",
                "is_default": config.set_as_default
            }
        else:
            raise HTTPException(status_code=400, detail=f"Failed to configure {config.exchange_name} exchange")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Configuration error: {str(e)}")

@api_router.get("/exchange/list")
async def list_exchanges():
    """List all configured exchanges and their status"""
    try:
        exchange_manager = get_exchange_manager()
        
        exchanges = exchange_manager.list_exchanges()
        status = exchange_manager.get_exchange_status()
        
        return {
            "exchanges": exchanges,
            "status": status,
            "default_exchange": exchange_manager.default_exchange
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing exchanges: {str(e)}")

@api_router.get("/exchange/market-data/{symbol}", response_model=RealMarketDataResponse)
async def get_real_market_data(symbol: str, exchange_name: Optional[str] = None):
    """Get real market data from configured exchange"""
    try:
        exchange_manager = get_exchange_manager()
        
        market_data = await exchange_manager.get_market_data(symbol, exchange_name)
        
        if not market_data:
            raise HTTPException(status_code=404, detail=f"Market data not available for {symbol}")
        
        return RealMarketDataResponse(
            symbol=market_data.symbol,
            timestamp=market_data.timestamp,
            price=market_data.price,
            bid=market_data.bid,
            ask=market_data.ask,
            volume=market_data.volume,
            high_24h=market_data.high_24h,
            low_24h=market_data.low_24h,
            change_24h=market_data.change_24h,
            exchange=exchange_name or exchange_manager.default_exchange or "unknown"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Market data error: {str(e)}")

@api_router.get("/exchange/market-data/{symbol}/best-price")
async def get_best_price(symbol: str, side: str):
    """Get best price across all configured exchanges"""
    try:
        exchange_manager = get_exchange_manager()
        
        if side.upper() not in ['BUY', 'SELL']:
            raise HTTPException(status_code=400, detail="Side must be BUY or SELL")
        
        best_price_info = await exchange_manager.get_best_price(symbol, side.upper())
        
        if not best_price_info:
            raise HTTPException(status_code=404, detail=f"No price data available for {symbol}")
        
        best_price, best_exchange = best_price_info
        
        return {
            "symbol": symbol,
            "side": side.upper(),
            "best_price": float(best_price),
            "best_exchange": best_exchange,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Price lookup error: {str(e)}")

@api_router.post("/exchange/order/market")
async def place_market_order(order: RealOrderRequest):
    """Place a market order on real exchange"""
    try:
        exchange_manager = get_exchange_manager()
        
        if order.side.upper() not in ['BUY', 'SELL']:
            raise HTTPException(status_code=400, detail="Side must be BUY or SELL")
        
        order_response = await exchange_manager.place_market_order(
            symbol=order.symbol,
            side=order.side.upper(),
            quantity=order.quantity,
            exchange_name=order.exchange_name
        )
        
        if not order_response:
            raise HTTPException(status_code=400, detail="Failed to place market order")
        
        return {
            "success": True,
            "order_id": order_response.order_id,
            "symbol": order_response.symbol,
            "side": order_response.side,
            "quantity": float(order_response.quantity),
            "price": float(order_response.price),
            "status": order_response.status,
            "timestamp": order_response.timestamp,
            "message": f"Market order placed successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Order placement error: {str(e)}")

@api_router.post("/exchange/order/limit")
async def place_limit_order(order: RealOrderRequest):
    """Place a limit order on real exchange"""
    try:
        exchange_manager = get_exchange_manager()
        
        if order.side.upper() not in ['BUY', 'SELL']:
            raise HTTPException(status_code=400, detail="Side must be BUY or SELL")
        
        if not order.price:
            raise HTTPException(status_code=400, detail="Price is required for limit orders")
        
        order_response = await exchange_manager.place_limit_order(
            symbol=order.symbol,
            side=order.side.upper(),
            quantity=order.quantity,
            price=order.price,
            exchange_name=order.exchange_name
        )
        
        if not order_response:
            raise HTTPException(status_code=400, detail="Failed to place limit order")
        
        return {
            "success": True,
            "order_id": order_response.order_id,
            "symbol": order_response.symbol,
            "side": order_response.side,
            "quantity": float(order_response.quantity),
            "price": float(order_response.price),
            "status": order_response.status,
            "timestamp": order_response.timestamp,
            "message": f"Limit order placed successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Order placement error: {str(e)}")

@api_router.delete("/exchange/order/{order_id}")
async def cancel_order(order_id: str, exchange_name: Optional[str] = None):
    """Cancel an order on real exchange"""
    try:
        exchange_manager = get_exchange_manager()
        
        success = await exchange_manager.cancel_order(order_id, exchange_name)
        
        return {
            "success": success,
            "order_id": order_id,
            "message": "Order cancelled successfully" if success else "Failed to cancel order"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Order cancellation error: {str(e)}")

@api_router.get("/exchange/balances")
async def get_account_balances(exchange_name: Optional[str] = None):
    """Get account balances from real exchange"""
    try:
        exchange_manager = get_exchange_manager()
        
        balances = await exchange_manager.get_account_balances(exchange_name)
        
        balance_data = []
        for balance in balances:
            balance_data.append({
                "currency": balance.currency,
                "available": float(balance.available),
                "locked": float(balance.locked),
                "total": float(balance.available + balance.locked)
            })
        
        return {
            "exchange": exchange_name or exchange_manager.default_exchange or "unknown",
            "balances": balance_data,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Balance retrieval error: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    # Disconnect from all exchanges
    exchange_manager = get_exchange_manager()
    await exchange_manager.disconnect_all()