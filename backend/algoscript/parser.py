from typing import List, Optional, Union
from .models import Token, TokenType, AlgoScriptAST, EventHandler, Condition, Action, IndicatorCall

class ParseError(Exception):
    def __init__(self, message: str, token: Optional[Token] = None):
        self.message = message
        self.token = token
        super().__init__(self.format_error())
    
    def format_error(self) -> str:
        if self.token:
            return f"{self.message} at line {self.token.line}, column {self.token.column}"
        return self.message

class AlgoScriptParser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0
        self.ast = AlgoScriptAST(symbol="", timeframe="")
    
    def parse(self) -> AlgoScriptAST:
        """
        Parse tokens into AST.
        """
        try:
            self._skip_newlines()
            
            # Parse SYMBOL declaration
            self._parse_symbol()
            self._skip_newlines()
            
            # Parse TIMEFRAME declaration
            self._parse_timeframe()
            self._skip_newlines()
            
            # Parse event handlers
            while not self._is_at_end() and self._peek().type != TokenType.END:
                if self._peek().type == TokenType.ON:
                    event_handler = self._parse_event_handler()
                    self.ast.event_handlers.append(event_handler)
                else:
                    self._advance()
                self._skip_newlines()
            
            return self.ast
            
        except ParseError:
            raise
        except Exception as e:
            raise ParseError(f"Unexpected error during parsing: {str(e)}")
    
    def _parse_symbol(self):
        """Parse SYMBOL declaration"""
        if not self._match(TokenType.SYMBOL):
            raise ParseError("Expected SYMBOL declaration", self._peek())
        
        if not self._peek().type == TokenType.STRING:
            raise ParseError("Expected symbol name as string", self._peek())
        
        self.ast.symbol = self._advance().value
    
    def _parse_timeframe(self):
        """Parse TIMEFRAME declaration"""
        if not self._match(TokenType.TIMEFRAME):
            raise ParseError("Expected TIMEFRAME declaration", self._peek())
        
        timeframe_token = self._advance()
        if timeframe_token.type in [TokenType.H4, TokenType.H1, TokenType.M15, TokenType.M5, TokenType.DAILY]:
            self.ast.timeframe = timeframe_token.value
        elif timeframe_token.type == TokenType.STRING:
            self.ast.timeframe = timeframe_token.value
        else:
            raise ParseError("Expected valid timeframe", timeframe_token)
    
    def _parse_event_handler(self) -> EventHandler:
        """Parse ON event handler"""
        if not self._match(TokenType.ON):
            raise ParseError("Expected ON keyword", self._peek())
        
        # Get event type
        event_token = self._advance()
        if event_token.type not in [TokenType.NEW_CANDLE, TokenType.ORDER_FILLED, TokenType.PRICE_CHANGE]:
            raise ParseError("Expected valid event type", event_token)
        
        if not self._match(TokenType.COLON):
            raise ParseError("Expected ':' after event type", self._peek())
        
        self._skip_newlines()
        
        handler = EventHandler(event_type=event_token.value)
        
        # Parse conditions and actions
        while not self._is_at_end() and self._peek().type not in [TokenType.ON, TokenType.END]:
            if self._peek().type == TokenType.IF:
                condition = self._parse_condition()
                handler.conditions.append(condition)
            elif self._peek().type in [TokenType.BUY, TokenType.SELL, TokenType.SET, TokenType.LOG]:
                action = self._parse_action()
                handler.actions.append(action)
            else:
                self._advance()
            self._skip_newlines()
        
        return handler
    
    def _parse_condition(self) -> Condition:
        """Parse IF condition"""
        if not self._match(TokenType.IF):
            raise ParseError("Expected IF keyword", self._peek())
        
        # Parse left side of condition
        left = self._parse_expression()
        
        # Parse operator
        operator_token = self._advance()
        operator = self._get_operator_string(operator_token)
        
        # Parse right side
        right = self._parse_expression()
        
        condition = Condition(left=left, operator=operator, right=right)
        
        # Check for logical operators (AND, OR)
        if self._peek().type in [TokenType.AND, TokenType.OR]:
            condition.logical_op = self._advance().value
        
        return condition
    
    def _parse_expression(self) -> Union[str, IndicatorCall, float]:
        """Parse expression (indicator, price, number, etc.)"""
        token = self._peek()
        
        if token.type == TokenType.PRICE:
            self._advance()
            return "PRICE"
        elif token.type in [TokenType.EMA, TokenType.RSI, TokenType.MACD, TokenType.MACD_HISTOGRAM]:
            return self._parse_indicator()
        elif token.type == TokenType.NUMBER:
            return float(self._advance().value)
        elif token.type == TokenType.PERCENTAGE:
            value = self._advance().value.rstrip('%')
            return float(value) / 100.0
        elif token.type == TokenType.ENTRY_PRICE:
            self._advance()
            return "ENTRY_PRICE"
        else:
            # Return as string for now
            return self._advance().value
    
    def _parse_indicator(self) -> IndicatorCall:
        """Parse indicator call like EMA(50) or MACD_HISTOGRAM(DAILY)"""
        indicator_token = self._advance()
        indicator_name = indicator_token.value
        
        if not self._match(TokenType.LPAREN):
            return IndicatorCall(name=indicator_name)
        
        # Parse parameter
        param_token = self._advance()
        
        if param_token.type == TokenType.NUMBER:
            period = int(float(param_token.value))
            if not self._match(TokenType.RPAREN):
                raise ParseError("Expected ')' after indicator parameter", self._peek())
            return IndicatorCall(name=indicator_name, period=period)
        elif param_token.type in [TokenType.DAILY, TokenType.H4, TokenType.H1, TokenType.M15, TokenType.M5]:
            timeframe = param_token.value
            if not self._match(TokenType.RPAREN):
                raise ParseError("Expected ')' after indicator parameter", self._peek())
            return IndicatorCall(name=indicator_name, timeframe=timeframe)
        else:
            raise ParseError("Expected valid indicator parameter", param_token)
    
    def _parse_action(self) -> Action:
        """Parse action (BUY, SELL, SET, LOG)"""
        action_token = self._advance()
        action_type = action_token.value
        
        parameters = {}
        
        if action_type == "BUY":
            parameters = self._parse_buy_action()
        elif action_type == "SELL":
            parameters = self._parse_sell_action()
        elif action_type == "SET":
            parameters = self._parse_set_action()
        elif action_type == "LOG":
            parameters = self._parse_log_action()
        
        return Action(type=action_type, parameters=parameters)
    
    def _parse_buy_action(self) -> dict:
        """Parse BUY action parameters"""
        params = {}
        
        # Parse amount (e.g., "50% OF BALANCE")
        if self._peek().type == TokenType.PERCENTAGE:
            percentage = float(self._advance().value.rstrip('%'))
            params['amount_percentage'] = percentage
            
            if self._match(TokenType.OF):
                if self._match(TokenType.BALANCE):
                    params['amount_type'] = 'BALANCE'
        elif self._peek().type == TokenType.NUMBER:
            params['amount'] = float(self._advance().value)
        
        # Parse order type
        if self._match(TokenType.WITH):
            order_type = self._advance()
            if order_type.type in [TokenType.MARKET_ORDER, TokenType.LIMIT_ORDER]:
                params['order_type'] = order_type.value
                
                # Parse limit order parameters
                if order_type.type == TokenType.LIMIT_ORDER and self._match(TokenType.AT):
                    # Parse limit price (e.g., "PRICE - 0.5%")
                    if self._match(TokenType.PRICE):
                        params['limit_base'] = 'PRICE'
                        # Look for +/- adjustment
                        # Simplified for now
                        params['limit_adjustment'] = 0.0
        
        return params
    
    def _parse_sell_action(self) -> dict:
        """Parse SELL action parameters"""
        params = {}
        
        # Parse amount
        if self._peek().type == TokenType.PERCENTAGE:
            percentage = float(self._advance().value.rstrip('%'))
            params['amount_percentage'] = percentage
            
            if self._match(TokenType.OF):
                if self._match(TokenType.POSITION):
                    params['amount_type'] = 'POSITION'
        
        # Parse order type
        if self._match(TokenType.WITH):
            order_type = self._advance()
            if order_type.type in [TokenType.MARKET_ORDER, TokenType.LIMIT_ORDER]:
                params['order_type'] = order_type.value
        
        return params
    
    def _parse_set_action(self) -> dict:
        """Parse SET action parameters"""
        params = {}
        
        # Parse what to set (STOP_LOSS, TAKE_PROFIT)
        target = self._advance()
        params['target'] = target.value
        
        if self._match(TokenType.AT):
            # Parse value (e.g., "5% BELOW ENTRY_PRICE")
            if self._peek().type == TokenType.PERCENTAGE:
                percentage = float(self._advance().value.rstrip('%'))
                params['percentage'] = percentage
                
                direction_token = self._advance()
                if direction_token.type in [TokenType.ABOVE, TokenType.BELOW]:
                    params['direction'] = direction_token.value
                    
                    base_token = self._advance()
                    params['base'] = base_token.value
        
        return params
    
    def _parse_log_action(self) -> dict:
        """Parse LOG action parameters"""
        params = {}
        
        if self._peek().type == TokenType.STRING:
            params['message'] = self._advance().value
        
        return params
    
    def _get_operator_string(self, token: Token) -> str:
        """Convert operator token to string"""
        if token.type == TokenType.CROSSES:
            # Need to check next token for UPWARDS/DOWNWARDS
            direction = self._advance()
            return f"CROSSES_{direction.value}"
        elif token.type == TokenType.IS:
            # Check next token for POSITIVE/NEGATIVE/LESS_THAN/etc
            condition = self._advance()
            return f"IS_{condition.value}"
        else:
            return token.value
    
    # Utility methods
    def _match(self, *types: TokenType) -> bool:
        """Check if current token matches any of the given types"""
        for token_type in types:
            if self._check(token_type):
                self._advance()
                return True
        return False
    
    def _check(self, token_type: TokenType) -> bool:
        """Check if current token is of given type"""
        if self._is_at_end():
            return False
        return self._peek().type == token_type
    
    def _advance(self) -> Token:
        """Consume current token and return it"""
        if not self._is_at_end():
            self.current += 1
        return self._previous()
    
    def _is_at_end(self) -> bool:
        """Check if we're at end of tokens"""
        return self.current >= len(self.tokens) or self._peek().type == TokenType.EOF
    
    def _peek(self) -> Token:
        """Return current token without advancing"""
        if self.current >= len(self.tokens):
            return Token(type=TokenType.EOF, value="", line=0, column=0)
        return self.tokens[self.current]
    
    def _previous(self) -> Token:
        """Return previous token"""
        if self.current > 0:
            return self.tokens[self.current - 1]
        return Token(type=TokenType.EOF, value="", line=0, column=0)
    
    def _skip_newlines(self):
        """Skip newline tokens"""
        while self._check(TokenType.NEWLINE):
            self._advance()