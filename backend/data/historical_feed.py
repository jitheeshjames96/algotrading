import yfinance as yf
import pandas as pd
import logging

def fetch_nse_data(ticker="^NSEI", interval="15m", period="45d"):
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        if df.empty: return None
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        df.reset_index(inplace=True)
        
        # SCHEMA NORMALIZER: Find the Date column regardless of what yfinance calls it
        date_candidates = ['date', 'datetime', 'index', 'timestamp']
        for col in df.columns:
            if col.lower() in date_candidates:
                df.rename(columns={col: 'timestamp'}, inplace=True)
                break
        
        df.columns = [c.lower() for c in df.columns]
        
        # Ensure 'timestamp' exists
        if 'timestamp' not in df.columns:
            logging.error(f"Mapping Failed. Available columns: {df.columns.tolist()}")
            return None
            
        return df[['timestamp', 'open', 'high', 'low', 'close']]
    except Exception as e:
        logging.error(f"Data Feed Error: {str(e)}")
        return None
