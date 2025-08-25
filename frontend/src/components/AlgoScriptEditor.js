import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AlgoScriptEditor = () => {
  const [code, setCode] = useState('');
  const [validationResult, setValidationResult] = useState(null);
  const [executionResult, setExecutionResult] = useState(null);
  const [marketData, setMarketData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [initialBalance, setInitialBalance] = useState(10000);

  // Load example code on component mount
  useEffect(() => {
    loadExampleCode();
    loadMarketData();
  }, []);

  const loadExampleCode = async () => {
    try {
      const response = await axios.get(`${API}/algoscript/example`);
      setCode(response.data.code);
    } catch (error) {
      console.error('Error loading example code:', error);
    }
  };

  const loadMarketData = async () => {
    try {
      const response = await axios.get(`${API}/algoscript/market-data/ETHUSD`);
      setMarketData(response.data);
    } catch (error) {
      console.error('Error loading market data:', error);
    }
  };

  const validateCode = async () => {
    try {
      setIsLoading(true);
      const response = await axios.post(`${API}/algoscript/validate`, {
        code: code
      });
      setValidationResult(response.data);
    } catch (error) {
      console.error('Error validating code:', error);
      setValidationResult({
        valid: false,
        errors: ['Network error: Could not validate code']
      });
    } finally {
      setIsLoading(false);
    }
  };

  const executeCode = async () => {
    try {
      setIsLoading(true);
      const response = await axios.post(`${API}/algoscript/execute`, {
        code: code,
        initial_balance: initialBalance,
        events: ['NEW_CANDLE']
      });
      setExecutionResult(response.data);
      
      // Refresh market data after execution
      await loadMarketData();
    } catch (error) {
      console.error('Error executing code:', error);
      setExecutionResult({
        success: false,
        error: 'Network error: Could not execute code'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const simulateNewCandle = async () => {
    try {
      await axios.post(`${API}/algoscript/market-data/ETHUSD/simulate-candle`);
      await loadMarketData();
    } catch (error) {
      console.error('Error simulating candle:', error);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">
          AlgoScript Trading Bot Platform
        </h1>
        <p className="text-lg text-gray-600">
          Create and test algorithmic trading strategies with human-readable syntax
        </p>
      </div>

      {/* Market Data Panel */}
      {marketData && (
        <div className="mb-6 bg-white rounded-lg shadow-md p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-gray-800">Market Data - {marketData.symbol}</h2>
            <button
              onClick={simulateNewCandle}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
            >
              Simulate New Candle
            </button>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="text-center">
              <div className="text-sm text-gray-500">Current Price</div>
              <div className="text-lg font-bold text-green-600">
                ${marketData.current_price.toFixed(2)}
              </div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-500">EMA(50)</div>
              <div className="text-lg font-bold text-blue-600">
                ${marketData.ema_50.toFixed(2)}
              </div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-500">RSI</div>
              <div className="text-lg font-bold text-purple-600">
                {marketData.rsi.toFixed(1)}
              </div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-500">MACD</div>
              <div className="text-lg font-bold text-orange-600">
                {marketData.macd.macd.toFixed(2)}
              </div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-500">Volume</div>
              <div className="text-lg font-bold text-gray-600">
                {marketData.volume.toFixed(0)}
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Code Editor Panel */}
        <div className="bg-white rounded-lg shadow-md">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-800">AlgoScript Editor</h2>
          </div>
          <div className="p-6">
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Initial Balance ($)
              </label>
              <input
                type="number"
                value={initialBalance}
                onChange={(e) => setInitialBalance(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                AlgoScript Code
              </label>
              <textarea
                value={code}
                onChange={(e) => setCode(e.target.value)}
                className="w-full h-96 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                placeholder="Enter your AlgoScript code here..."
              />
            </div>
            
            <div className="flex gap-3">
              <button
                onClick={validateCode}
                disabled={isLoading}
                className="px-4 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600 transition-colors disabled:opacity-50"
              >
                {isLoading ? 'Validating...' : 'Validate'}
              </button>
              <button
                onClick={executeCode}
                disabled={isLoading || !code.trim()}
                className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 transition-colors disabled:opacity-50"
              >
                {isLoading ? 'Executing...' : 'Execute'}
              </button>
              <button
                onClick={loadExampleCode}
                className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors"
              >
                Load Example
              </button>
            </div>
          </div>
        </div>

        {/* Results Panel */}
        <div className="bg-white rounded-lg shadow-md">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-800">Results</h2>
          </div>
          <div className="p-6">
            {/* Validation Results */}
            {validationResult && (
              <div className="mb-6">
                <h3 className="text-lg font-medium text-gray-800 mb-3">Validation</h3>
                <div className={`p-3 rounded-md ${
                  validationResult.valid 
                    ? 'bg-green-50 border border-green-200' 
                    : 'bg-red-50 border border-red-200'
                }`}>
                  <div className={`font-medium ${
                    validationResult.valid ? 'text-green-800' : 'text-red-800'
                  }`}>
                    {validationResult.valid ? '✓ Valid' : '✗ Invalid'}
                  </div>
                  
                  {validationResult.errors && validationResult.errors.length > 0 && (
                    <div className="mt-2">
                      <div className="text-sm font-medium text-red-700">Errors:</div>
                      <ul className="text-sm text-red-600 ml-4 list-disc">
                        {validationResult.errors.map((error, index) => (
                          <li key={index}>{error}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  {validationResult.warnings && validationResult.warnings.length > 0 && (
                    <div className="mt-2">
                      <div className="text-sm font-medium text-yellow-700">Warnings:</div>
                      <ul className="text-sm text-yellow-600 ml-4 list-disc">
                        {validationResult.warnings.map((warning, index) => (
                          <li key={index}>{warning}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Execution Results */}
            {executionResult && (
              <div className="mb-6">
                <h3 className="text-lg font-medium text-gray-800 mb-3">Execution</h3>
                <div className={`p-3 rounded-md ${
                  executionResult.success 
                    ? 'bg-green-50 border border-green-200' 
                    : 'bg-red-50 border border-red-200'
                }`}>
                  <div className={`font-medium ${
                    executionResult.success ? 'text-green-800' : 'text-red-800'
                  }`}>
                    {executionResult.success ? '✓ Executed Successfully' : '✗ Execution Failed'}
                  </div>
                  
                  {executionResult.error && (
                    <div className="mt-2 text-sm text-red-600">
                      Error: {executionResult.error}
                    </div>
                  )}
                </div>

                {/* Trading State */}
                {executionResult.trading_state && (
                  <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
                    <h4 className="font-medium text-blue-800 mb-2">Trading State</h4>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="text-blue-600">Balance:</span> 
                        <span className="font-medium ml-1">
                          ${executionResult.trading_state.balance.toFixed(2)}
                        </span>
                      </div>
                      <div>
                        <span className="text-blue-600">Position:</span> 
                        <span className="font-medium ml-1">
                          {executionResult.trading_state.position_size.toFixed(4)}
                        </span>
                      </div>
                      {executionResult.trading_state.entry_price && (
                        <div>
                          <span className="text-blue-600">Entry Price:</span> 
                          <span className="font-medium ml-1">
                            ${executionResult.trading_state.entry_price.toFixed(2)}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Execution Logs */}
                {executionResult.logs && executionResult.logs.length > 0 && (
                  <div className="mt-4">
                    <h4 className="font-medium text-gray-800 mb-2">Execution Logs</h4>
                    <div className="bg-gray-900 text-green-400 p-3 rounded-md text-xs font-mono max-h-64 overflow-y-auto">
                      {executionResult.logs.map((log, index) => (
                        <div key={index} className="mb-1">{log}</div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Documentation Panel */}
      <div className="mt-8 bg-white rounded-lg shadow-md">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-800">AlgoScript Documentation</h2>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div>
              <h3 className="font-medium text-gray-800 mb-2">Basic Structure</h3>
              <div className="text-sm text-gray-600 font-mono bg-gray-50 p-2 rounded">
                SYMBOL "ETHUSD"<br/>
                TIMEFRAME "4H"<br/><br/>
                ON NEW_CANDLE:<br/>
                &nbsp;&nbsp;LOG "Hello"<br/><br/>
                END
              </div>
            </div>
            
            <div>
              <h3 className="font-medium text-gray-800 mb-2">Events</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• NEW_CANDLE</li>
                <li>• ORDER_FILLED</li>
                <li>• PRICE_CHANGE</li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-medium text-gray-800 mb-2">Indicators</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• EMA(period)</li>
                <li>• RSI(period)</li>
                <li>• MACD()</li>
                <li>• MACD_HISTOGRAM()</li>
                <li>• PRICE</li>
                <li>• VOLUME</li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-medium text-gray-800 mb-2">Actions</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• BUY amount OF BALANCE</li>
                <li>• SELL amount OF POSITION</li>
                <li>• SET STOP_LOSS AT price</li>
                <li>• SET TAKE_PROFIT AT price</li>
                <li>• LOG "message"</li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-medium text-gray-800 mb-2">Conditions</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• IF condition</li>
                <li>• AND / OR</li>
                <li>• CROSSES UPWARDS/DOWNWARDS</li>
                <li>• IS POSITIVE/NEGATIVE</li>
                <li>• LESS_THAN / GREATER_THAN</li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-medium text-gray-800 mb-2">Order Types</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• MARKET_ORDER</li>
                <li>• LIMIT_ORDER</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AlgoScriptEditor;