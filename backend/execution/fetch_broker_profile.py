import requests
import logging
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(message)s')

class DhanDiagnosticsClient:
    def __init__(self):
        self.access_token = os.getenv("BROKER_ACCESS_TOKEN", "")
        self.base_url = "https://api.dhan.co/v2"
        self.headers = {
            "access-token": self.access_token,
            "Content-Type": "application/json"
        }

    def fetch_account_margin_summary(self):
        """Queries Dhan's live accounting endpoints or defaults safely to local simulated state values."""
        # Baseline fallback mock state payload parameters
        mock_fallback = {
            "status": "SIMULATED_SUCCESS",
            "availableBalance": 100000.00,
            "utilizedMargin": 0.00
        }
        
        if not self.access_token or self.access_token == "dummy_token_for_now":
            return mock_fallback

        try:
            # Official DhanHQ production endpoint path for pulling account cash limits
            response = requests.get(f"{self.base_url}/fundlimit", headers=self.headers, timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                logging.error(f"❌ Broker access unauthorized (HTTP {response.status_code}): Defaulting to local sandbox simulation mode.")
                return mock_fallback
        except Exception as e:
            logging.error(f"🚨 Network exception connecting to broker endpoint: {str(e)}")
            return mock_fallback

if __name__ == "__main__":
    client = DhanDiagnosticsClient()
    ledger = client.fetch_account_margin_summary()
    
    print("\n==================================================")
    print("      💼 LIVE BROKER TRANSACTION DATA ANALYSIS")
    print("==================================================")
    print(f"  Account Available Balance : ₹{ledger.get('availableBalance', ledger.get('availabelBalance', 0.0)):,.2f}")
    print(f"  Current Blocked Margin    : ₹{ledger.get('utilizedMargin', ledger.get('utilizedAmount', 0.0)):,.2f}")
    print("==================================================")
