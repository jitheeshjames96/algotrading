import os
import logging
from fyers_apiv3 import fyersModel
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

class FyersExecutionManager:
    def __init__(self):
        # Secure credential sanitization
        self.client_id = os.getenv("FYERS_CLIENT_ID", "").strip()
        self.access_token = os.getenv("FYERS_ACCESS_TOKEN", "").strip()
        
        if ":" in self.access_token:
            self.access_token = self.access_token.split(":")[-1]
        if not self.client_id.endswith("-100"):
            self.client_id = f"{self.client_id}-100"
            
        # Initialize Fyers API Gateway
        self.fyers = fyersModel.FyersModel(
            client_id=self.client_id,
            token=self.access_token,
            is_async=False,
            log_path=""
        )

    def execute_market_order(self, derivative_symbol: str, action: str, qty: int):
        """
        Fires a low-latency Market Order to the NSE.
        action: 'BUY' or 'SELL'
        """
        side = 1 if action.upper() == 'BUY' else -1
        
        data = {
            "symbol": derivative_symbol,
            "qty": qty,
            "type": 2,  # 2 = Market Order
            "side": side, 
            "productType": "INTRADAY", # Enforces intraday margins
            "limitPrice": 0,
            "stopPrice": 0,
            "validity": "DAY",
            "disclosedQty": 0,
            "offlineOrder": False,
        }
        
        try:
            logging.info(f"⚡ DISPATCHING ORDER | {action} {qty}x {derivative_symbol}")
            response = self.fyers.place_order(data=data)
            
            if response.get('s') == 'ok':
                order_id = response.get('id')
                logging.info(f"✅ ORDER FILLED | ID: {order_id}")
                return order_id
            else:
                logging.error(f"❌ REJECTED BY EXCHANGE | Reason: {response.get('message')}")
                return None
                
        except Exception as e:
            logging.critical(f"API Execution Failure: {str(e)}")
            return None

    def emergency_kill_switch(self):
        """
        Production Safety: Immediately closes all open intraday positions at Market price.
        """
        logging.warning("🚨 INITIATING EMERGENCY KILL SWITCH 🚨")
        try:
            # Passing empty dict {} tells Fyers to exit all open positions across all segments
            response = self.fyers.exit_positions(data={}) 
            
            if response.get('s') == 'ok':
                logging.info("✅ ALL OPEN POSITIONS FLATTENED. SYSTEM SAFE.")
            else:
                logging.error(f"❌ KILL SWITCH FAILED: {response.get('message')}")
        except Exception as e:
            logging.critical(f"KILL SWITCH EXCEPTION: {str(e)}")

if __name__ == "__main__":
    # Smoke Test
    manager = FyersExecutionManager()
    # manager.execute_market_order("NSE:NIFTY24JUNFUT", "BUY", 25)
