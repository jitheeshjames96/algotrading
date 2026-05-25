import requests
import pandas as pd
import io
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(message)s')

class ProductionTokenManager:
    def __init__(self):
        self.csv_url = "https://images.dhan.co/api-data/api-scrip-master.csv"
        self.storage_path = "/Users/jitheesh.pj/Desktop/Jitheesh/algo/backend/config/scrip_master.parquet"

    def fetch_and_sync_tokens(self) -> bool:
        """Downloads the daily security master from Dhan and adapts to their explicit database layout."""
        logging.info("📥 Downloading latest daily NSE Security Token Master list from Dhan...")
        try:
            response = requests.get(self.csv_url, timeout=30)
            if response.status_code != 200:
                logging.error(f"❌ Failed to fetch scrip master: HTTP {response.status_code}")
                return False

            raw_data = response.content.decode('utf-8')
            df = pd.read_csv(io.StringIO(raw_data), dtype=str)

            # Strip spaces and uppercase columns to maintain zero-variance matching strings
            df.columns = [col.strip().upper() for col in df.columns]
            
            # Explicit definitions mapping directly to your system dump:
            exch_col = 'SEM_EXM_EXCH_ID'
            
            if exch_col not in df.columns:
                logging.error(f"❌ Target column missing. Total available structural keys: {list(df.columns)}")
                return False

            # Filter exclusively for National Stock Exchange Futures & Options segment
            fo_df = df[df[exch_col].str.upper() == 'NSE_FO'].copy()
            
            # Locate the exact trading symbol column inside the payload matrix dynamically
            symbol_col = None
            for candidate in ['SEM_TRADING_SYMBOL', 'SEM_CUSTOM_SYMBOL', 'SEM_SMST_TRADING_SYMBOL', 'TRADINGSYMBOL']:
                if candidate in fo_df.columns:
                    symbol_col = candidate
                    break
                    
            if not symbol_col:
                # If it's none of those, find any string matching a column layout name
                symbol_cols = [c for c in fo_df.columns if 'SYMBOL' in c]
                if symbol_cols:
                    symbol_col = symbol_cols[0]
            
            if symbol_col:
                fo_df[symbol_col] = fo_df[symbol_col].str.strip().str.upper()
                logging.info(f"🔗 Linked Symbol matching engine tracker to column: {symbol_col}")

            # Write high-speed binary snappified parquet files
            fo_df.to_parquet(self.storage_path, compression='snappy')
            logging.info(f"✅ Token Master Synced. Cached {len(fo_df)} active derivative contracts inside local storage partition.")
            return True
        except Exception as e:
            logging.critical(f"🚨 Token synchronization pipeline collapsed: {str(e)}")
            return False

    def lookup_option_token(self, trading_symbol: str) -> str:
        """Queries the high-speed local data frame for absolute contract token mapping matches."""
        if not os.path.exists(self.storage_path):
            logging.error("Scrip master file missing. Attempting emergency synchronization...")
            if not self.fetch_and_sync_tokens():
                return "0"

        try:
            df = pd.read_parquet(self.storage_path)
            
            # Identify internal primary token identification mapping keys
            id_col = 'SEM_SMST_SECURITY_ID' if 'SEM_SMST_SECURITY_ID' in df.columns else 'SEM_SM_ID'
            
            # Loop through any symbol columns to locate the exact option contract target text tag
            symbol_cols = [c for c in df.columns if 'SYMBOL' in c]
            
            for col in symbol_cols:
                match = df[df[col] == trading_symbol.upper()]
                if not match.empty:
                    return str(match.iloc[0][id_col])
                    
            logging.warning(f"⚠️ Token contract mapping missed for symbol string: {trading_symbol}")
            return "0"
        except Exception as e:
            logging.error(f"Failed to query cached token data frame: {str(e)}")
            return "0"

if __name__ == "__main__":
    manager = ProductionTokenManager()
    success = manager.fetch_and_sync_tokens()
    if success:
        # Check an arbitrary test contract string format lookup
        token_id = manager.lookup_option_token("NIFTY24MAY24050CE")
        print(f"\n⚡ Token Query Verification Result -> Resolved ID Code: {token_id}")
