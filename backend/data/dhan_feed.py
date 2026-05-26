# /backend/data/dhan_feed.py
from dhanhq import dhanhq
import pandas as pd
import os

def get_live_nifty_data():
    # Load from environment variables
    client = dhanhq(os.getenv("DHAN_CLIENT_ID"), os.getenv("DHAN_ACCESS_TOKEN"))
    
    # Fetch 15min timeframe Nifty data
    data = client.intradaytimeSeriesData(
        symbol="NIFTY 50", exchangeSegment="IDX_I", 
        instrument="INDEX", timeFrame="15"
    )
    # Convert to DataFrame... (logic remains as discussed)
    return pd.DataFrame(data['data'])
