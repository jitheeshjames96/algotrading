import yfinance as yf
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

def fetch_nse_data(ticker="RELIANCE.NS", interval="15m", period="5d"):
    """Fetches historical OHLCV data for NSE stocks."""
    logging.info(f"Fetching {period} of {interval} data for {ticker}...")
    
    df = yf.download(ticker, period=period, interval=interval, progress=False)
    
    if df.empty:
        logging.error(f"Failed to fetch data for {ticker}.")
        return None
        
    df.reset_index(inplace=True)
    
    # yfinance sometimes returns multi-level columns in newer versions, let's flatten them if needed
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
        
    # Standardize column names for our SMC engine
    df.rename(columns={'Datetime': 'timestamp', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'}, inplace=True)
    
    # Ensure columns are lowercase just in case
    df.columns = [col.lower() for col in df.columns]
    
    return df

if __name__ == "__main__":
    df = fetch_nse_data()
    print(df.tail())
