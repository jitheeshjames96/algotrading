import os
from dotenv import load_dotenv

load_dotenv()

# PRODUCTION CONTROL PANEL
# Change this to True ONLY when your real Dhan Client ID and active tokens are configured
IS_LIVE_TRADING = False 

BROKER_CREDENTIALS = {
    "API_KEY": os.getenv("BROKER_API_KEY", ""),
    "API_SECRET": os.getenv("BROKER_API_SECRET", ""),
    "ACCESS_TOKEN": os.getenv("BROKER_ACCESS_TOKEN", ""),
    "DHAN_CLIENT_ID": os.getenv("DHAN_CLIENT_ID", "1200000000") # Your real 10-digit Dhan ID goes here
}

ASSET_REGISTRY = {
    "NIFTY": {
        "ticker": "^NSEI",
        "ema_period": 50,
        "atr_period": 14,
        "atr_multiplier": 1.5,
        "step_value": 50
    }
}
