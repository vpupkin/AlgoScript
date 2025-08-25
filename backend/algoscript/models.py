from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum
import uuid

class TokenType(Enum):
    # Literals
    SYMBOL = "SYMBOL"
    TIMEFRAME = "TIMEFRAME"
    NUMBER = "NUMBER"
    STRING = "STRING"
    PERCENTAGE = "PERCENTAGE"
    
    # Keywords
    ON = "ON"
    IF = "IF"
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    END = "END"
    SET = "SET"
    LOG = "LOG"
    
    # Events
    NEW_CANDLE = "NEW_CANDLE"
    ORDER_FILLED = "ORDER_FILLED"
    PRICE_CHANGE = "PRICE_CHANGE"
    
    # Indicators
    PRICE = "PRICE"
    EMA = "EMA"
    RSI = "RSI"
    MACD = "MACD"
    MACD_HISTOGRAM = "MACD_HISTOGRAM"
    VOLUME = "VOLUME"
    
    # Actions
    BUY = "BUY"
    SELL = "SELL"
    MARKET_ORDER = "MARKET_ORDER"
    LIMIT_ORDER = "LIMIT_ORDER"
    
    # Position Management
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"
    ENTRY_PRICE = "ENTRY_PRICE"
    BALANCE = "BALANCE"
    POSITION = "POSITION"
    
    # Operators
    CROSSES = "CROSSES"
    UPWARDS = "UPWARDS"
    DOWNWARDS = "DOWNWARDS"
    IS = "IS"
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    LESS_THAN = "LESS_THAN"
    GREATER_THAN = "GREATER_THAN"
    AT = "AT"
    OF = "OF"
    WITH = "WITH"
    ABOVE = "ABOVE"
    BELOW = "BELOW"
    
    # Timeframes
    DAILY = "DAILY"
    H4 = "4H"
    H1 = "1H"
    M15 = "15M"
    M5 = "5M"
    
    # Punctuation
    COLON = "COLON"
    COMMA = "COMMA"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    NEWLINE = "NEWLINE"
    
    # Special
    EOF = "EOF"
    UNKNOWN = "UNKNOWN"

class Token(BaseModel):
    type: TokenType
    value: str
    line: int
    column: int

class IndicatorCall(BaseModel):
    name: str
    period: Optional[int] = None
    timeframe: Optional[str] = None

class Condition(BaseModel):
    left: Union[str, IndicatorCall]
    operator: str
    right: Union[str, IndicatorCall, float]
    logical_op: Optional[str] = None  # AND, OR

class Action(BaseModel):
    type: str  # BUY, SELL, SET, LOG
    parameters: Dict[str, Any] = Field(default_factory=dict)

class EventHandler(BaseModel):
    event_type: str  # NEW_CANDLE, ORDER_FILLED, PRICE_CHANGE
    conditions: List[Condition] = Field(default_factory=list)
    actions: List[Action] = Field(default_factory=list)

class AlgoScriptAST(BaseModel):
    symbol: str
    timeframe: str
    event_handlers: List[EventHandler] = Field(default_factory=list)
    global_variables: Dict[str, Any] = Field(default_factory=dict)

class MarketData(BaseModel):
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

class TradingState(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str
    position_size: float = 0.0
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    balance: float = 10000.0  # Starting balance
    variables: Dict[str, Any] = Field(default_factory=dict)
    orders: List[Dict[str, Any]] = Field(default_factory=list)
    logs: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ExecutionResult(BaseModel):
    success: bool
    logs: List[str] = Field(default_factory=list)
    trading_state: Optional[TradingState] = None
    error: Optional[str] = None
    executed_actions: List[str] = Field(default_factory=list)

class AlgoScriptRequest(BaseModel):
    code: str
    symbol: Optional[str] = "ETHUSD"
    initial_balance: Optional[float] = 10000.0

class ValidationResult(BaseModel):
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    ast: Optional[AlgoScriptAST] = None
</content>
    </file>