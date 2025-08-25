from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
from .models import (
    AlgoScriptAST, EventHandler, Condition, Action, 
    TradingState, ExecutionResult, IndicatorCall
)
from .market_data import get_market_data, MockMarketData

logger = logging.getLogger(__name__)

class AlgoScriptExecutor:
    """
    Executes AlgoScript AST and manages trading state.
    """
    
    def __init__(self, ast: AlgoScriptAST, initial_balance: float = 10000.0):
        self.ast = ast
        self.trading_state = TradingState(
            symbol=ast.symbol,
            balance=initial_balance
        )
        self.market_data = get_market_data(ast.symbol)
        self.execution_logs = []
        self.executed_actions = []
    
    def execute(self, event_type: str = "NEW_CANDLE") -> ExecutionResult:
        """
        Execute the AlgoScript for a specific event.
        """
        try:
            self.execution_logs = []
            self.executed_actions = []
            
            self.log(f"=== AlgoScript Execution Started ===")
            self.log(f"Symbol: {self.ast.symbol}, Timeframe: {self.ast.timeframe}")
            self.log(f"Event: {event_type}")
            self.log(f"Current Price: ${self.market_data.get_current_price():.2f}")
            self.log(f"Balance: ${self.trading_state.balance:.2f}")
            
            if self.trading_state.position_size > 0:
                self.log(f"Position: {self.trading_state.position_size:.4f} @ ${self.trading_state.entry_price:.2f}")
            
            # Find matching event handlers
            matching_handlers = [
                handler for handler in self.ast.event_handlers 
                if handler.event_type == event_type
            ]
            
            if not matching_handlers:
                self.log(f"No handlers found for event: {event_type}")
                return self._create_result(True)
            
            # Execute each matching handler
            for handler in matching_handlers:
                self._execute_event_handler(handler)
            
            self.log("=== AlgoScript Execution Completed ===")
            
            return self._create_result(True)
            
        except Exception as e:
            error_msg = f"Execution error: {str(e)}"
            self.log(error_msg)
            logger.error(error_msg, exc_info=True)
            return self._create_result(False, error_msg)
    
    def _execute_event_handler(self, handler: EventHandler):
        """Execute a specific event handler"""
        self.log(f"\n--- Processing {handler.event_type} handler ---")
        
        # Check conditions
        if handler.conditions:
            conditions_met = True
            for condition in handler.conditions:
                if not self._evaluate_condition(condition):
                    conditions_met = False
                    break
            
            if not conditions_met:
                self.log("Conditions not met, skipping actions")
                return
        
        # Execute actions
        for action in handler.actions:
            self._execute_action(action)
    
    def _evaluate_condition(self, condition: Condition) -> bool:
        """Evaluate a trading condition"""
        try:
            left_value = self._resolve_value(condition.left)
            right_value = self._resolve_value(condition.right)
            
            self.log(f"Evaluating: {condition.left} {condition.operator} {condition.right}")
            self.log(f"Values: {left_value} {condition.operator} {right_value}")
            
            result = self._apply_operator(left_value, condition.operator, right_value)
            
            self.log(f"Condition result: {result}")
            return result
            
        except Exception as e:
            self.log(f"Error evaluating condition: {str(e)}")
            return False
    
    def _resolve_value(self, value: Any) -> float:
        """Resolve a value (indicator, price, number, etc.) to a float"""
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            if value == "PRICE":
                return self.market_data.get_current_price()
            elif value == "ENTRY_PRICE":
                return self.trading_state.entry_price or 0.0
            elif value == "BALANCE":
                return self.trading_state.balance
            # Add more string value resolutions as needed
            
        if isinstance(value, IndicatorCall):
            return self._calculate_indicator(value)
        
        # Try to convert to float
        try:
            return float(str(value))
        except:
            return 0.0
    
    def _calculate_indicator(self, indicator: IndicatorCall) -> float:
        """Calculate indicator value"""
        if indicator.name == "EMA":
            period = indicator.period or 50
            return self.market_data.calculate_ema(period)
        
        elif indicator.name == "RSI":
            period = indicator.period or 14
            return self.market_data.calculate_rsi(period)
        
        elif indicator.name == "MACD":
            macd_data = self.market_data.calculate_macd()
            return macd_data["macd"]
        
        elif indicator.name == "MACD_HISTOGRAM":
            macd_data = self.market_data.calculate_macd()
            return macd_data["histogram"]
        
        elif indicator.name == "VOLUME":
            return self.market_data.get_volume()
        
        return 0.0
    
    def _apply_operator(self, left: float, operator: str, right: float) -> bool:
        """Apply comparison operator"""
        if operator == "CROSSES_UPWARDS":
            # Simplified: check if left > right (assuming cross happened)
            indicator_value = right
            return self.market_data.check_price_cross(left, indicator_value, "UPWARDS")
        
        elif operator == "CROSSES_DOWNWARDS":
            indicator_value = right
            return self.market_data.check_price_cross(left, indicator_value, "DOWNWARDS")
        
        elif operator == "IS_POSITIVE":
            return left > 0
        
        elif operator == "IS_NEGATIVE":
            return left < 0
        
        elif operator == "LESS_THAN" or operator == "IS_LESS_THAN":
            return left < right
        
        elif operator == "GREATER_THAN" or operator == "IS_GREATER_THAN":
            return left > right
        
        elif operator == "IS":
            return abs(left - right) < 0.001  # Approximate equality
        
        return False
    
    def _execute_action(self, action: Action):
        """Execute a trading action"""
        action_type = action.type
        params = action.parameters
        
        self.log(f"\nExecuting action: {action_type}")
        
        if action_type == "BUY":
            self._execute_buy_action(params)
        elif action_type == "SELL":
            self._execute_sell_action(params)
        elif action_type == "SET":
            self._execute_set_action(params)
        elif action_type == "LOG":
            self._execute_log_action(params)
        
        self.executed_actions.append(f"{action_type}: {params}")
    
    def _execute_buy_action(self, params: Dict[str, Any]):
        """Execute BUY action"""
        current_price = self.market_data.get_current_price()
        
        # Calculate amount to buy
        if 'amount_percentage' in params and params.get('amount_type') == 'BALANCE':
            percentage = params['amount_percentage'] / 100.0
            dollar_amount = self.trading_state.balance * percentage
            quantity = dollar_amount / current_price
        elif 'amount' in params:
            quantity = params['amount']
            dollar_amount = quantity * current_price
        else:
            self.log("Invalid BUY parameters")
            return
        
        if dollar_amount > self.trading_state.balance:
            self.log(f"Insufficient balance. Required: ${dollar_amount:.2f}, Available: ${self.trading_state.balance:.2f}")
            return
        
        order_type = params.get('order_type', 'MARKET_ORDER')
        
        if order_type == "LIMIT_ORDER":
            # Handle limit order logic (simplified)
            limit_price = current_price  # Simplified
            self.log(f"BUY LIMIT ORDER: {quantity:.4f} {self.ast.symbol} at ${limit_price:.2f}")
            execution_price = limit_price
        else:
            self.log(f"BUY MARKET ORDER: {quantity:.4f} {self.ast.symbol} at ${current_price:.2f}")
            execution_price = current_price
        
        # Update trading state
        self.trading_state.position_size += quantity
        self.trading_state.entry_price = execution_price
        self.trading_state.balance -= dollar_amount
        
        # Record order
        order = {
            "type": "BUY",
            "order_type": order_type,
            "quantity": quantity,
            "price": execution_price,
            "timestamp": datetime.utcnow(),
            "status": "FILLED"
        }
        self.trading_state.orders.append(order)
        
        self.log(f"Order executed: {quantity:.4f} @ ${execution_price:.2f}")
        self.log(f"New position: {self.trading_state.position_size:.4f}")
        self.log(f"Remaining balance: ${self.trading_state.balance:.2f}")
    
    def _execute_sell_action(self, params: Dict[str, Any]):
        """Execute SELL action"""
        if self.trading_state.position_size <= 0:
            self.log("No position to sell")
            return
        
        current_price = self.market_data.get_current_price()
        
        # Calculate amount to sell
        if 'amount_percentage' in params and params.get('amount_type') == 'POSITION':
            percentage = params['amount_percentage'] / 100.0
            quantity = self.trading_state.position_size * percentage
        elif 'amount' in params:
            quantity = min(params['amount'], self.trading_state.position_size)
        else:
            quantity = self.trading_state.position_size
        
        order_type = params.get('order_type', 'MARKET_ORDER')
        
        self.log(f"SELL {order_type}: {quantity:.4f} {self.ast.symbol} at ${current_price:.2f}")
        
        # Calculate P&L
        if self.trading_state.entry_price:
            pnl = (current_price - self.trading_state.entry_price) * quantity
            pnl_percentage = ((current_price / self.trading_state.entry_price) - 1) * 100
            self.log(f"P&L: ${pnl:.2f} ({pnl_percentage:+.2f}%)")
        
        # Update trading state
        self.trading_state.position_size -= quantity
        self.trading_state.balance += quantity * current_price
        
        if self.trading_state.position_size <= 0:
            self.trading_state.entry_price = None
            self.trading_state.stop_loss = None
            self.trading_state.take_profit = None
        
        # Record order
        order = {
            "type": "SELL",
            "order_type": order_type,
            "quantity": quantity,
            "price": current_price,
            "timestamp": datetime.utcnow(),
            "status": "FILLED"
        }
        self.trading_state.orders.append(order)
        
        self.log(f"Position sold: {quantity:.4f} @ ${current_price:.2f}")
        self.log(f"Remaining position: {self.trading_state.position_size:.4f}")
        self.log(f"New balance: ${self.trading_state.balance:.2f}")
    
    def _execute_set_action(self, params: Dict[str, Any]):
        """Execute SET action (stop loss, take profit)"""
        target = params.get('target')
        
        if target == "STOP_LOSS":
            percentage = params.get('percentage', 0)
            direction = params.get('direction', 'BELOW')
            base = params.get('base', 'ENTRY_PRICE')
            
            if base == "ENTRY_PRICE" and self.trading_state.entry_price:
                if direction == "BELOW":
                    stop_loss = self.trading_state.entry_price * (1 - percentage / 100.0)
                else:
                    stop_loss = self.trading_state.entry_price * (1 + percentage / 100.0)
                
                self.trading_state.stop_loss = stop_loss
                self.log(f"STOP_LOSS set at ${stop_loss:.2f} ({percentage}% {direction} entry price)")
        
        elif target == "TAKE_PROFIT":
            percentage = params.get('percentage', 0)
            direction = params.get('direction', 'ABOVE')
            base = params.get('base', 'ENTRY_PRICE')
            
            if base == "ENTRY_PRICE" and self.trading_state.entry_price:
                if direction == "ABOVE":
                    take_profit = self.trading_state.entry_price * (1 + percentage / 100.0)
                else:
                    take_profit = self.trading_state.entry_price * (1 - percentage / 100.0)
                
                self.trading_state.take_profit = take_profit
                self.log(f"TAKE_PROFIT set at ${take_profit:.2f} ({percentage}% {direction} entry price)")
    
    def _execute_log_action(self, params: Dict[str, Any]):
        """Execute LOG action"""
        message = params.get('message', '')
        self.log(f"STRATEGY LOG: {message}")
    
    def check_stop_loss_take_profit(self) -> List[str]:
        """Check if stop loss or take profit should be triggered"""
        triggered_actions = []
        current_price = self.market_data.get_current_price()
        
        if self.trading_state.position_size > 0:
            # Check stop loss
            if (self.trading_state.stop_loss and 
                current_price <= self.trading_state.stop_loss):
                
                self.log(f"STOP LOSS TRIGGERED at ${current_price:.2f}")
                self._execute_sell_action({
                    'amount_percentage': 100,
                    'amount_type': 'POSITION',
                    'order_type': 'MARKET_ORDER'
                })
                triggered_actions.append("STOP_LOSS")
            
            # Check take profit
            elif (self.trading_state.take_profit and 
                  current_price >= self.trading_state.take_profit):
                
                self.log(f"TAKE PROFIT TRIGGERED at ${current_price:.2f}")
                self._execute_sell_action({
                    'amount_percentage': 100,
                    'amount_type': 'POSITION',
                    'order_type': 'MARKET_ORDER'
                })
                triggered_actions.append("TAKE_PROFIT")
        
        return triggered_actions
    
    def simulate_event(self, event_type: str) -> ExecutionResult:
        """Simulate a specific market event"""
        if event_type == "NEW_CANDLE":
            self.market_data.generate_new_candle()
        elif event_type == "PRICE_CHANGE":
            # Simulate small price change
            change = (-1 if self.market_data.get_current_price() > 2000 else 1) * 0.5
            self.market_data.simulate_price_change(change)
        elif event_type == "ORDER_FILLED":
            # This would be triggered after a buy/sell order
            pass
        
        # Check stop loss / take profit
        self.check_stop_loss_take_profit()
        
        return self.execute(event_type)
    
    def log(self, message: str):
        """Add message to execution logs"""
        timestamp = datetime.utcnow().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.execution_logs.append(formatted_message)
        self.trading_state.logs.append(formatted_message)
        logger.info(formatted_message)
    
    def _create_result(self, success: bool, error: Optional[str] = None) -> ExecutionResult:
        """Create execution result"""
        return ExecutionResult(
            success=success,
            logs=self.execution_logs.copy(),
            trading_state=self.trading_state,
            error=error,
            executed_actions=self.executed_actions.copy()
        )