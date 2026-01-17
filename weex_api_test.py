"""
WEEX API Test Script for AI Wars: WEEX Alpha Awakens Hackathon
Official Demo Code from WEEX Documentation
https://www.weex.com/api-doc/ai/QuickStart/RequestInteraction
"""

import time
import hmac
import hashlib
import base64
import requests
import json

# =============================================================================
# CONFIGURATION - Your API Credentials
# =============================================================================
api_key = "weex_a5ca1f88c85b9eefaed3a954e7e91867"
secret_key = "c7270ae5f736e1fc2345d716a299482c017c7bc5639f4e7a0d866ef9a570e02e"
access_passphrase = "weex26647965"

# API Base URL (Official from WEEX docs)
BASE_URL = "https://api-contract.weex.com/"

# Trading pair
SYMBOL = "cmt_btcusdt"

# =============================================================================
# SIGNATURE GENERATION (Exact copy from WEEX official demo)
# =============================================================================

def generate_signature(secret_key, timestamp, method, request_path, query_string, body):
    """Generate signature for POST requests"""
    message = timestamp + method.upper() + request_path + query_string + str(body)
    signature = hmac.new(secret_key.encode(), message.encode(), hashlib.sha256).digest()
    return base64.b64encode(signature).decode()


def generate_signature_get(secret_key, timestamp, method, request_path, query_string):
    """Generate signature for GET requests"""
    message = timestamp + method.upper() + request_path + query_string
    signature = hmac.new(secret_key.encode(), message.encode(), hashlib.sha256).digest()
    return base64.b64encode(signature).decode()


# =============================================================================
# REQUEST FUNCTIONS (Exact copy from WEEX official demo)
# =============================================================================

def send_request_post(api_key, secret_key, access_passphrase, method, request_path, query_string, body):
    """Send POST request"""
    timestamp = str(int(time.time() * 1000))
    body = json.dumps(body)
    signature = generate_signature(secret_key, timestamp, method, request_path, query_string, body)
    
    headers = {
        "ACCESS-KEY": api_key,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": access_passphrase,
        "Content-Type": "application/json",
        "locale": "en-US"
    }
    
    url = BASE_URL
    if method == "GET":
        response = requests.get(url + request_path, headers=headers, timeout=30)
    elif method == "POST":
        response = requests.post(url + request_path, headers=headers, data=body, timeout=30)
    
    return response


def send_request_get(api_key, secret_key, access_passphrase, method, request_path, query_string):
    """Send GET request"""
    timestamp = str(int(time.time() * 1000))
    signature = generate_signature_get(secret_key, timestamp, method, request_path, query_string)
    
    headers = {
        "ACCESS-KEY": api_key,
        "ACCESS-SIGN": signature,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": access_passphrase,
        "Content-Type": "application/json",
        "locale": "en-US"
    }
    
    url = BASE_URL
    if method == "GET":
        response = requests.get(url + request_path + query_string, headers=headers, timeout=30)
    
    return response


# =============================================================================
# API TEST FUNCTIONS
# =============================================================================

def test_connectivity():
    """Test basic connectivity to WEEX API"""
    print("\n" + "="*60)
    print("🔍 Testing API Connectivity")
    print("="*60)
    
    try:
        response = requests.get(BASE_URL, timeout=10)
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text[:200] if response.text else 'No content'}")
        return response.status_code
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


def get_position():
    """Step 3: Get account position (from official demo)"""
    print("\n" + "="*60)
    print("📊 STEP 3: Getting Account Position")
    print("="*60)
    
    request_path = "/capi/v2/account/position/singlePosition"
    query_string = f'?symbol={SYMBOL}'
    
    try:
        response = send_request_get(api_key, secret_key, access_passphrase, "GET", request_path, query_string)
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        return response
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


def get_account():
    """Get account info"""
    print("\n" + "="*60)
    print("📊 Getting Account Info")
    print("="*60)
    
    request_path = "/capi/v2/account/accounts"
    query_string = f'?symbol={SYMBOL}'
    
    try:
        response = send_request_get(api_key, secret_key, access_passphrase, "GET", request_path, query_string)
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        return response
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


def set_leverage(leverage=10):
    """Step 4: Set leverage"""
    print("\n" + "="*60)
    print(f"⚙️ STEP 4: Setting Leverage to {leverage}x")
    print("="*60)
    
    request_path = "/capi/v2/account/changeLeverage"
    body = {
        "symbol": SYMBOL,
        "leverage": str(leverage),
        "side": "1"
    }
    query_string = ""
    
    try:
        response = send_request_post(api_key, secret_key, access_passphrase, "POST", request_path, query_string, body)
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        return response
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


def get_ticker():
    """Step 5: Get current price (public endpoint)"""
    print("\n" + "="*60)
    print("💰 STEP 5: Getting Asset Price (BTC/USDT)")
    print("="*60)
    
    url = f"{BASE_URL}capi/v2/market/ticker?symbol={SYMBOL}"
    
    try:
        response = requests.get(url, timeout=30)
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        return response
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


def place_order(size="0.01", order_type="1", match_price="1"):
    """Step 6-8: Place order (from official demo)"""
    print("\n" + "="*60)
    print("📝 STEP 6-8: Placing Order")
    print("="*60)
    
    request_path = "/capi/v2/order/placeOrder"
    client_oid = str(int(time.time() * 1000))
    
    body = {
        "symbol": SYMBOL,
        "client_oid": client_oid,
        "size": size,
        "type": order_type,      # 1=Open Long, 2=Open Short
        "order_type": "0",       # 0=Normal
        "match_price": match_price,  # 1=Market price
        "price": "80000"         # Price (for limit orders)
    }
    query_string = ""
    
    print(f"   Order Details:")
    print(f"   - Symbol: {SYMBOL}")
    print(f"   - Size: {size}")
    print(f"   - Type: {'Open Long' if order_type == '1' else 'Open Short' if order_type == '2' else order_type}")
    print(f"   - Match Price: {'Market' if match_price == '1' else 'Limit'}")
    print(f"   - Client OID: {client_oid}")
    
    try:
        response = send_request_post(api_key, secret_key, access_passphrase, "POST", request_path, query_string, body)
        print(f"\n   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        return response
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


def get_current_orders():
    """Step 9: Get current/open orders"""
    print("\n" + "="*60)
    print("📋 STEP 9: Getting Current Orders")
    print("="*60)
    
    request_path = "/capi/v2/order/currentOrders"
    query_string = f'?symbol={SYMBOL}'
    
    try:
        response = send_request_get(api_key, secret_key, access_passphrase, "GET", request_path, query_string)
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        return response
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


def get_order_history():
    """Step 10: Get order history"""
    print("\n" + "="*60)
    print("📜 STEP 10: Getting Order History")
    print("="*60)
    
    request_path = "/capi/v2/order/historyOrders"
    query_string = f'?symbol={SYMBOL}&pageSize=20&pageNo=1'
    
    try:
        response = send_request_get(api_key, secret_key, access_passphrase, "GET", request_path, query_string)
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        return response
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


def get_fills():
    """Step 11: Get trade fills/details"""
    print("\n" + "="*60)
    print("📊 STEP 11: Getting Trade Details (Fills)")
    print("="*60)
    
    request_path = "/capi/v2/order/fills"
    query_string = f'?symbol={SYMBOL}&pageSize=20&pageNo=1'
    
    try:
        response = send_request_get(api_key, secret_key, access_passphrase, "GET", request_path, query_string)
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        return response
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def run_full_test():
    """Run complete API test sequence"""
    print("\n" + "="*70)
    print("🚀 WEEX API TEST - AI Wars: WEEX Alpha Awakens Hackathon")
    print("="*70)
    print(f"\nConfiguration:")
    print(f"   API Key: {api_key[:15]}...")
    print(f"   Base URL: {BASE_URL}")
    print(f"   Symbol: {SYMBOL}")
    print()
    
    # Test connectivity first
    status = test_connectivity()
    if status == 521:
        print("\n⚠️ Error 521: Origin server is down or refusing connection")
        print("   This could be due to:")
        print("   1. Your IP is not whitelisted with WEEX")
        print("   2. The API server is temporarily down")
        print("   3. Geographic restriction")
        print("\n   Please contact WEEX hackathon support for assistance.")
        return
    
    # Step 3: Get Account/Position
    get_account()
    get_position()
    
    # Step 4: Set Leverage
    set_leverage(10)
    
    # Step 5: Get Price
    get_ticker()
    
    # Step 6-8: Place Order (0.01 BTC at market price)
    place_order(size="0.01", order_type="1", match_price="1")
    
    print("\n⏳ Waiting 3 seconds for order to process...")
    time.sleep(3)
    
    # Step 9: Get Current Orders
    get_current_orders()
    
    # Step 10: Get Order History
    get_order_history()
    
    # Step 11: Get Fills
    get_fills()
    
    print("\n" + "="*70)
    print("✅ API TEST COMPLETED!")
    print("="*70)


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║       AI Wars: WEEX Alpha Awakens - Official Demo Code          ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║  1. Run Full API Test                                           ║
    ║  2. Test Connectivity Only                                      ║
    ║  3. Get Account Info Only                                       ║
    ║  4. Place Order Only                                            ║
    ║  5. Exit                                                        ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    choice = input("Select option (1-5): ").strip()
    
    if choice == "1":
        run_full_test()
    elif choice == "2":
        test_connectivity()
    elif choice == "3":
        get_account()
        get_position()
    elif choice == "4":
        place_order()
    elif choice == "5":
        print("Goodbye!")
    else:
        print("Running full test...")
        run_full_test()
