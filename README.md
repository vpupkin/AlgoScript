# AlgoScript Trading Bot Platform

A domain-specific language (DSL) for creating algorithmic trading bots with human-readable syntax. Write trading strategies in plain English and execute them with real-time market simulation.

## 🚀 Features

- **Human-Readable Syntax**: Write trading strategies in natural English
- **Event-Driven Architecture**: Respond to market events (NEW_CANDLE, ORDER_FILLED, PRICE_CHANGE)
- **Built-in Trading Concepts**: Native support for indicators (EMA, RSI, MACD), orders, and risk management
- **Real-time Market Simulation**: Mock market data with realistic price movements and indicators
- **Web-based Editor**: Interactive code editor with validation and execution
- **Comprehensive Logging**: Detailed execution logs and trading state tracking

## 📋 Prerequisites

- Python 3.8+
- Node.js 16+
- MongoDB (configured via environment variables)

## 🛠️ Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd algoscript-trading-platform
```

### 2. Backend Setup
```bash
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env  # Edit with your MongoDB connection
```

### 3. Frontend Setup
```bash
cd frontend

# Install Node.js dependencies
yarn install

# Set up environment variables
cp .env.example .env  # Edit with your backend URL
```

## 🚀 How to Run

### Method 1: Using Supervisor (Recommended)

The platform uses supervisor to manage both frontend and backend services:

```bash
# Start all services
sudo supervisorctl start all

# Check status
sudo supervisorctl status

# Restart services
sudo supervisorctl restart all

# Stop all services
sudo supervisorctl stop all
```

### Method 2: Manual Start

#### Start Backend
```bash
cd backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

#### Start Frontend
```bash
cd frontend
yarn start
```

## 🌐 Access the Platform

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs

## 📖 AlgoScript Language Guide

### Basic Structure
```algoscript
SYMBOL "ETHUSD" TIMEFRAME "4H"

ON NEW_CANDLE:
    LOG "New candle received"

END
```

### Complete Example
```algoscript
SYMBOL "ETHUSD" TIMEFRAME "4H"

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

END
```

### Language Elements

#### Events
- `NEW_CANDLE` - Triggered when a new price candle is formed
- `ORDER_FILLED` - Triggered when an order is executed
- `PRICE_CHANGE` - Triggered on price movements

#### Indicators
- `EMA(period)` - Exponential Moving Average
- `RSI(period)` - Relative Strength Index  
- `MACD()` - Moving Average Convergence Divergence
- `MACD_HISTOGRAM()` - MACD Histogram
- `PRICE` - Current market price
- `VOLUME` - Current volume

#### Actions
- `BUY amount OF BALANCE WITH order_type` - Place buy order
- `SELL amount OF POSITION WITH order_type` - Place sell order
- `SET STOP_LOSS AT price` - Set stop loss level
- `SET TAKE_PROFIT AT price` - Set take profit level
- `LOG "message"` - Log a message

#### Conditions
- `IF condition` - Conditional execution
- `AND` / `OR` - Logical operators
- `CROSSES UPWARDS/DOWNWARDS` - Price crossing indicators
- `IS POSITIVE/NEGATIVE` - Value comparisons
- `LESS_THAN` / `GREATER_THAN` - Numeric comparisons

## 🔧 API Endpoints

### Core Endpoints
- `GET /api/` - API status
- `GET /api/algoscript/example` - Get example AlgoScript code
- `POST /api/algoscript/validate` - Validate AlgoScript syntax
- `POST /api/algoscript/execute` - Execute AlgoScript strategy
- `POST /api/algoscript/execute-multi` - Execute with multiple events

### Market Data
- `GET /api/algoscript/market-data/{symbol}` - Get current market data
- `POST /api/algoscript/market-data/{symbol}/simulate-candle` - Simulate new candle

## 🧪 Testing

### Backend Testing
```bash
cd backend
python -c "from algoscript.interpreter import get_interpreter; print('✓ AlgoScript interpreter ready')"
```

### Frontend Testing
```bash
cd frontend
yarn test
```

### API Testing
```bash
# Test API endpoints
curl http://localhost:8001/api/algoscript/example
curl -X POST http://localhost:8001/api/algoscript/validate \
  -H "Content-Type: application/json" \
  -d '{"code": "SYMBOL \"ETHUSD\" TIMEFRAME \"4H\"\n\nON NEW_CANDLE:\n    LOG \"Hello World\"\n\nEND"}'
```

## 📁 Project Structure

```
algoscript-trading-platform/
├── backend/
│   ├── algoscript/
│   │   ├── lexer.py          # AlgoScript tokenizer
│   │   ├── parser.py         # AST parser
│   │   ├── executor.py       # Strategy executor
│   │   ├── interpreter.py    # Main interpreter
│   │   ├── models.py         # Data models
│   │   └── market_data.py    # Market simulation
│   ├── server.py             # FastAPI server
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── AlgoScriptEditor.js  # Main UI component
│   │   └── App.js            # React app
│   └── package.json          # Node.js dependencies
└── README.md                 # This file
```

## 🐛 Troubleshooting

### Common Issues

1. **Backend not starting**
   ```bash
   # Check supervisor logs
   tail -n 100 /var/log/supervisor/backend.*.log
   
   # Restart backend service
   sudo supervisorctl restart backend
   ```

2. **Frontend not loading**
   ```bash
   # Check if backend URL is correct in frontend/.env
   echo $REACT_APP_BACKEND_URL
   
   # Restart frontend service
   sudo supervisorctl restart frontend
   ```

3. **AlgoScript validation errors**
   - Check syntax against the language guide above
   - Use the web interface validation feature
   - Check execution logs for detailed error messages

### Service Management
```bash
# Check all services
sudo supervisorctl status

# View logs
sudo supervisorctl tail -f backend
sudo supervisorctl tail -f frontend

# Restart specific service
sudo supervisorctl restart backend
sudo supervisurctl restart frontend
```

## 🎯 Usage Examples

### 1. Simple Logging Strategy
```algoscript
SYMBOL "BTCUSD" TIMEFRAME "1H"

ON NEW_CANDLE:
    LOG "New Bitcoin candle at price: " 

END
```

### 2. RSI-based Strategy
```algoscript
SYMBOL "ETHUSD" TIMEFRAME "4H"

ON NEW_CANDLE:
    IF RSI(14) IS LESS_THAN 30
        BUY 25% OF BALANCE WITH MARKET_ORDER
        LOG "RSI oversold, buying ETH"

END
```

### 3. Moving Average Crossover
```algoscript
SYMBOL "ETHUSD" TIMEFRAME "4H"

ON NEW_CANDLE:
    IF PRICE CROSSES EMA(20) UPWARDS
        BUY 50% OF BALANCE WITH MARKET_ORDER
        SET STOP_LOSS AT 3% BELOW ENTRY_PRICE
        SET TAKE_PROFIT AT 6% ABOVE ENTRY_PRICE
        LOG "Golden cross detected"

END
```

## 📈 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙋‍♂️ Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the AlgoScript language guide
3. Test with the provided examples
4. Check service logs for detailed error information

---

**Happy Trading with AlgoScript! 🚀📈**
