from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime

# AlgoScript imports
from algoscript.interpreter import get_interpreter
from algoscript.models import AlgoScriptRequest, ValidationResult, ExecutionResult
from algoscript.market_data import get_market_data

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="AlgoScript Trading Bot Platform", version="1.0.0")

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

class MarketDataResponse(BaseModel):
    symbol: str
    current_price: float
    ema_50: float
    rsi: float
    macd: dict
    volume: float

# Original routes
@api_router.get("/")
async def root():
    return {"message": "AlgoScript Trading Bot Platform API"}

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

# AlgoScript routes
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
    """Execute AlgoScript code and return results"""
    try:
        interpreter = get_interpreter()
        
        # Convert to AlgoScriptRequest
        algo_request = AlgoScriptRequest(
            code=request.code,
            initial_balance=request.initial_balance
        )
        
        if len(request.events) == 1:
            # Single event execution
            result = interpreter.execute(algo_request)
            return result
        else:
            # Multi-event execution - return the last result
            results = interpreter.execute_with_events(algo_request, request.events)
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
        
        results = interpreter.execute_with_events(algo_request, request.events)
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")

@api_router.get("/algoscript/example")
async def get_example_code():
    """Get example AlgoScript code"""
    interpreter = get_interpreter()
    return {"code": interpreter.get_example_code()}

@api_router.get("/algoscript/market-data/{symbol}", response_model=MarketDataResponse)
async def get_market_data_api(symbol: str = "ETHUSD"):
    """Get current market data for a symbol"""
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