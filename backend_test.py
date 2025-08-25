import requests
import sys
import json
from datetime import datetime

class AlgoScriptAPITester:
    def __init__(self, base_url="https://trading-lang.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Non-dict response'}")
                    return True, response_data
                except:
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timeout")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        return self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200
        )

    def test_get_example_code(self):
        """Test getting example AlgoScript code"""
        success, response = self.run_test(
            "Get Example Code",
            "GET",
            "algoscript/example",
            200
        )
        
        if success and isinstance(response, dict) and 'code' in response:
            print(f"   Example code length: {len(response['code'])} characters")
            return True, response['code']
        return False, ""

    def test_validate_algoscript(self, code):
        """Test AlgoScript validation"""
        return self.run_test(
            "Validate AlgoScript",
            "POST",
            "algoscript/validate",
            200,
            data={"code": code}
        )

    def test_execute_algoscript(self, code):
        """Test AlgoScript execution"""
        return self.run_test(
            "Execute AlgoScript",
            "POST",
            "algoscript/execute",
            200,
            data={
                "code": code,
                "initial_balance": 10000.0,
                "events": ["NEW_CANDLE"]
            }
        )

    def test_get_market_data(self):
        """Test getting market data"""
        return self.run_test(
            "Get Market Data",
            "GET",
            "algoscript/market-data/ETHUSD",
            200
        )

    def test_simulate_candle(self):
        """Test simulating new candle"""
        return self.run_test(
            "Simulate New Candle",
            "POST",
            "algoscript/market-data/ETHUSD/simulate-candle",
            200
        )

    def test_custom_algoscript(self):
        """Test the specific AlgoScript code from the request"""
        custom_code = '''SYMBOL "ETHUSD" TIMEFRAME "4H"

ON NEW_CANDLE:
    LOG "Testing AlgoScript execution"
    BUY 25% OF BALANCE WITH MARKET_ORDER
    SET STOP_LOSS AT 5% BELOW ENTRY_PRICE

END'''
        
        print(f"\n🧪 Testing Custom AlgoScript Code:")
        print(f"   Code:\n{custom_code}")
        
        # First validate
        success, validation_result = self.test_validate_algoscript(custom_code)
        if not success:
            print("❌ Custom code validation failed")
            return False
        
        if isinstance(validation_result, dict) and not validation_result.get('valid', False):
            print(f"❌ Custom code is invalid: {validation_result.get('errors', [])}")
            return False
        
        # Then execute
        success, execution_result = self.test_execute_algoscript(custom_code)
        if not success:
            print("❌ Custom code execution failed")
            return False
        
        # Check execution results
        if isinstance(execution_result, dict):
            if execution_result.get('success'):
                print("✅ Custom code executed successfully")
                
                # Check trading state
                trading_state = execution_result.get('trading_state')
                if trading_state:
                    print(f"   Balance: ${trading_state.get('balance', 0):.2f}")
                    print(f"   Position: {trading_state.get('position_size', 0):.4f}")
                    if trading_state.get('entry_price'):
                        print(f"   Entry Price: ${trading_state.get('entry_price'):.2f}")
                
                # Check logs
                logs = execution_result.get('logs', [])
                if logs:
                    print(f"   Execution logs ({len(logs)} entries):")
                    for log in logs[:3]:  # Show first 3 logs
                        print(f"     - {log}")
                
                return True
            else:
                print(f"❌ Custom code execution failed: {execution_result.get('error', 'Unknown error')}")
        
        return False

def main():
    print("🚀 Starting AlgoScript Trading Bot Platform API Tests")
    print("=" * 60)
    
    tester = AlgoScriptAPITester()
    
    # Test 1: Root endpoint
    tester.test_root_endpoint()
    
    # Test 2: Get example code
    success, example_code = tester.test_get_example_code()
    if not success:
        print("❌ Cannot proceed without example code")
        return 1
    
    # Test 3: Validate example code
    tester.test_validate_algoscript(example_code)
    
    # Test 4: Execute example code
    tester.test_execute_algoscript(example_code)
    
    # Test 5: Get market data
    tester.test_get_market_data()
    
    # Test 6: Simulate new candle
    tester.test_simulate_candle()
    
    # Test 7: Test custom AlgoScript from request
    tester.test_custom_algoscript()
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())