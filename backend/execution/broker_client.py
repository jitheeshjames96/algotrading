import requests
import time
import logging
from config.broker_config import BROKER_CREDENTIALS, IS_LIVE_TRADING

logging.basicConfig(level=logging.INFO, format='%(message)s')

class DhanBrokerClient:
    def __init__(self):
        self.api_key = BROKER_CREDENTIALS["API_KEY"]
        self.access_token = BROKER_CREDENTIALS["ACCESS_TOKEN"]
        self.client_id = BROKER_CREDENTIALS["DHAN_CLIENT_ID"]
        self.base_url = "https://api.dhan.co/v2" 
        
        self.headers = {
            "access-token": self.access_token,
            "Content-Type": "application/json"
        }

    def place_options_market_order(self, security_id: str, symbol: str, quantity: int, transaction_type: str):
        """
        Dispatches an instantaneous Market Order for an Options Contract to Dhan or executes a clean local simulation.
        """
        # SAFEGUARD GATE: If live mode is turned off, catch execution locally and log a mock transaction
        if not IS_LIVE_TRADING:
            logging.warning(f"⚠️ [PAPER FILL] | {transaction_type} | {quantity} Qty | Contract: {symbol} | Token ID: {security_id}")
            return {"status": "SUCCESS", "orderId": "SIMULATED_ORDER_OK"}

        endpoint = f"{self.base_url}/orders"
        
        payload = {
            "dhanClientId": str(self.client_id),
            "correlationId": f"SMC_{int(time.time())}", 
            "transactionType": transaction_type.upper(), 
            "exchangeSegment": "NSE_FO",
            "productType": "INTRA", 
            "orderType": "MARKET",
            "validity": "DAY",
            "tradingSymbol": symbol.upper(),
            "securityId": str(security_id), 
            "quantity": int(quantity)
        }

        try:
            response = requests.post(endpoint, json=payload, headers=self.headers, timeout=5)
            if response.status_code == 200:
                order_data = response.json()
                logging.info(f"✅ REAL EXECUTION SUCCESS | Order ID: {order_data.get('orderId')}")
                return order_data
            else:
                logging.error(f"❌ BROKER REJECTION | HTTP {response.status_code} | Code: {response.json().get('errorCode')} | Detail: {response.json().get('errorMessage')}")
                return None
        except Exception as e:
            logging.critical(f"🚨 GATEWAY CONNECTIVITY ERROR: {str(e)}")
            return None

if __name__ == "__main__":
    client = DhanBrokerClient()
    client.place_options_market_order(security_id="35000", symbol="NIFTY24MAY24050CE", quantity=75, transaction_type="BUY")
