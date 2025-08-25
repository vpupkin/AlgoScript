import re
from typing import List, Optional
from .models import Token, TokenType

class AlgoScriptLexer:
    def __init__(self):
        # Define token patterns
        self.token_patterns = [
            # String literals (must come before keywords)
            (r'"([^"]*)"', TokenType.STRING),
            
            # Numbers and percentages
            (r'\d+\.?\d*%', TokenType.PERCENTAGE),
            (r'\d+\.?\d*', TokenType.NUMBER),
            
            # Keywords and identifiers (order matters!)
            (r'\bSYMBOL\b', TokenType.SYMBOL),
            (r'\bTIMEFRAME\b', TokenType.TIMEFRAME),
            (r'\bON\b', TokenType.ON),
            (r'\bIF\b', TokenType.IF),
            (r'\bAND\b', TokenType.AND),
            (r'\bOR\b', TokenType.OR),
            (r'\bNOT\b', TokenType.NOT),
            (r'\bEND\b', TokenType.END),
            (r'\bSET\b', TokenType.SET),
            (r'\bLOG\b', TokenType.LOG),
            
            # Events
            (r'\bNEW_CANDLE\b', TokenType.NEW_CANDLE),
            (r'\bORDER_FILLED\b', TokenType.ORDER_FILLED),
            (r'\bPRICE_CHANGE\b', TokenType.PRICE_CHANGE),
            
            # Indicators
            (r'\bPRICE\b', TokenType.PRICE),
            (r'\bEMA\b', TokenType.EMA),
            (r'\bRSI\b', TokenType.RSI),
            (r'\bMACD_HISTOGRAM\b', TokenType.MACD_HISTOGRAM),
            (r'\bMACD\b', TokenType.MACD),
            (r'\bVOLUME\b', TokenType.VOLUME),
            
            # Actions
            (r'\bBUY\b', TokenType.BUY),
            (r'\bSELL\b', TokenType.SELL),
            (r'\bMARKET_ORDER\b', TokenType.MARKET_ORDER),
            (r'\bLIMIT_ORDER\b', TokenType.LIMIT_ORDER),
            
            # Position Management
            (r'\bSTOP_LOSS\b', TokenType.STOP_LOSS),
            (r'\bTAKE_PROFIT\b', TokenType.TAKE_PROFIT),
            (r'\bENTRY_PRICE\b', TokenType.ENTRY_PRICE),
            (r'\bBALANCE\b', TokenType.BALANCE),
            (r'\bPOSITION\b', TokenType.POSITION),
            
            # Operators
            (r'\bCROSSES\b', TokenType.CROSSES),
            (r'\bUPWARDS\b', TokenType.UPWARDS),
            (r'\bDOWNWARDS\b', TokenType.DOWNWARDS),
            (r'\bIS\b', TokenType.IS),
            (r'\bPOSITIVE\b', TokenType.POSITIVE),
            (r'\bNEGATIVE\b', TokenType.NEGATIVE),
            (r'\bLESS\s+THAN\b', TokenType.LESS_THAN),
            (r'\bGREATER\s+THAN\b', TokenType.GREATER_THAN),
            (r'\bAT\b', TokenType.AT),
            (r'\bOF\b', TokenType.OF),
            (r'\bWITH\b', TokenType.WITH),
            (r'\bABOVE\b', TokenType.ABOVE),
            (r'\bBELOW\b', TokenType.BELOW),
            
            # Timeframes
            (r'\bDAILY\b', TokenType.DAILY),
            (r'\b4H\b', TokenType.H4),
            (r'\b1H\b', TokenType.H1),
            (r'\b15M\b', TokenType.M15),
            (r'\b5M\b', TokenType.M5),
            
            # Punctuation
            (r':', TokenType.COLON),
            (r',', TokenType.COMMA),
            (r'\(', TokenType.LPAREN),
            (r'\)', TokenType.RPAREN),
            (r'\n', TokenType.NEWLINE),
            
            # Skip whitespace (except newlines)
            (r'[ \t]+', None),
            
            # Skip comments
            (r'#.*', None),
        ]
        
        # Compile patterns
        self.compiled_patterns = [(re.compile(pattern), token_type) 
                                 for pattern, token_type in self.token_patterns]
    
    def tokenize(self, code: str) -> List[Token]:
        """
        Tokenize AlgoScript code into a list of tokens.
        """
        tokens = []
        lines = code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            column = 1
            pos = 0
            
            while pos < len(line):
                match_found = False
                
                for pattern, token_type in self.compiled_patterns:
                    match = pattern.match(line, pos)
                    if match:
                        matched_text = match.group(0)
                        
                        # Skip whitespace and comments
                        if token_type is None:
                            pos = match.end()
                            column += len(matched_text)
                            match_found = True
                            break
                        
                        # Handle string literals (remove quotes)
                        if token_type == TokenType.STRING:
                            value = match.group(1)  # Extract content without quotes
                        else:
                            value = matched_text
                        
                        tokens.append(Token(
                            type=token_type,
                            value=value,
                            line=line_num,
                            column=column
                        ))
                        
                        pos = match.end()
                        column += len(matched_text)
                        match_found = True
                        break
                
                if not match_found:
                    # Unknown character
                    tokens.append(Token(
                        type=TokenType.UNKNOWN,
                        value=line[pos],
                        line=line_num,
                        column=column
                    ))
                    pos += 1
                    column += 1
            
            # Add newline token at end of each line (except last if empty)
            if line_num < len(lines) or line.strip():
                tokens.append(Token(
                    type=TokenType.NEWLINE,
                    value='\n',
                    line=line_num,
                    column=len(line) + 1
                ))
        
        # Add EOF token
        tokens.append(Token(
            type=TokenType.EOF,
            value='',
            line=len(lines),
            column=1
        ))
        
        return tokens
    
    def validate_tokens(self, tokens: List[Token]) -> List[str]:
        """
        Validate tokens and return list of errors.
        """
        errors = []
        
        for token in tokens:
            if token.type == TokenType.UNKNOWN:
                errors.append(f"Unknown token '{token.value}' at line {token.line}, column {token.column}")
        
        return errors