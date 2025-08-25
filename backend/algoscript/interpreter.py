from typing import List, Optional
import logging
from .lexer import AlgoScriptLexer
from .parser import AlgoScriptParser, ParseError
from .executor import AlgoScriptExecutor
from .models import ValidationResult, ExecutionResult, AlgoScriptRequest

logger = logging.getLogger(__name__)

class AlgoScriptInterpreter:
    """
    Main AlgoScript interpreter that combines lexer, parser, and executor.
    """
    
    def __init__(self):
        self.lexer = AlgoScriptLexer()
    
    def validate(self, code: str) -> ValidationResult:
        """
        Validate AlgoScript code without executing it.
        Returns validation result with errors and warnings.
        """
        try:
            # Tokenize
            tokens = self.lexer.tokenize(code)
            lexer_errors = self.lexer.validate_tokens(tokens)
            
            if lexer_errors:
                return ValidationResult(
                    valid=False,
                    errors=lexer_errors
                )
            
            # Parse
            parser = AlgoScriptParser(tokens)
            ast = parser.parse()
            
            # Additional semantic validation
            warnings = []
            
            # Check if required declarations are present
            if not ast.symbol:
                warnings.append("No SYMBOL declaration found")
            
            if not ast.timeframe:
                warnings.append("No TIMEFRAME declaration found")
            
            if not ast.event_handlers:
                warnings.append("No event handlers defined")
            
            return ValidationResult(
                valid=True,
                errors=[],
                warnings=warnings,
                ast=ast
            )
            
        except ParseError as e:
            return ValidationResult(
                valid=False,
                errors=[str(e)]
            )
        except Exception as e:
            return ValidationResult(
                valid=False,
                errors=[f"Unexpected validation error: {str(e)}"]
            )
    
    def execute(self, request: AlgoScriptRequest) -> ExecutionResult:
        """
        Execute AlgoScript code and return execution result.
        """
        try:
            # First validate
            validation = self.validate(request.code)
            if not validation.valid:
                return ExecutionResult(
                    success=False,
                    error=f"Validation failed: {', '.join(validation.errors)}"
                )
            
            # Create executor
            executor = AlgoScriptExecutor(
                ast=validation.ast,
                initial_balance=request.initial_balance
            )
            
            # Execute the script
            result = executor.execute("NEW_CANDLE")
            
            return result
            
        except Exception as e:
            logger.error(f"Execution error: {str(e)}", exc_info=True)
            return ExecutionResult(
                success=False,
                error=f"Execution error: {str(e)}"
            )
    
    def execute_with_events(self, request: AlgoScriptRequest, events: List[str]) -> List[ExecutionResult]:
        """
        Execute AlgoScript code with multiple events in sequence.
        """
        results = []
        
        try:
            # First validate
            validation = self.validate(request.code)
            if not validation.valid:
                error_result = ExecutionResult(
                    success=False,
                    error=f"Validation failed: {', '.join(validation.errors)}"
                )
                return [error_result]
            
            # Create executor
            executor = AlgoScriptExecutor(
                ast=validation.ast,
                initial_balance=request.initial_balance
            )
            
            # Execute each event
            for event in events:
                result = executor.simulate_event(event)
                results.append(result)
                
                # Stop if there's an error
                if not result.success:
                    break
            
            return results
            
        except Exception as e:
            logger.error(f"Multi-event execution error: {str(e)}", exc_info=True)
            error_result = ExecutionResult(
                success=False,
                error=f"Execution error: {str(e)}"
            )
            return [error_result]
    
    def get_example_code(self) -> str:
        """
        Return the example AlgoScript code for testing.
        """
        return '''SYMBOL "ETHUSD" TIMEFRAME "4H"

ON NEW_CANDLE:
    IF PRICE CROSSES EMA(50) UPWARDS AND MACD_HISTOGRAM(DAILY) IS POSITIVE
        BUY 50% OF BALANCE WITH MARKET_ORDER
        SET STOP_LOSS AT 5% BELOW ENTRY_PRICE
        LOG "BUY SIGNAL: Golden Cross confirmed by MACD."

ON ORDER_FILLED:
    SET TAKE_PROFIT AT 10% ABOVE ENTRY_PRICE
    LOG "ORDER FILLED. Take-Profit set."

ON PRICE_CHANGE:
    IF PRICE IS LESS_THAN ENTRY_PRICE
        SELL 100% OF POSITION WITH MARKET_ORDER
        LOG "STOP_LOSS triggered."

END'''

# Global interpreter instance
interpreter_instance = AlgoScriptInterpreter()

def get_interpreter() -> AlgoScriptInterpreter:
    """Get the global interpreter instance"""
    return interpreter_instance