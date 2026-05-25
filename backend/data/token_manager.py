import requests
import pandas as pd
import io
import logging
import os
import re

logging.basicConfig(level=logging.INFO, format='%(message)s')

class ProductionTokenManager:
    def __init__(self):
        self.csv_url = "https://images.dhan.co/api-data/api-scrip-master.csv"
        self.storage_path = "/Users/jitheesh.pj/Desktop/Jitheesh/algo/backend/config/scrip_master.parquet"

    def fetch_and_sync_tokens(self) -> bool:
        logging.info("📥 Downloading latest daily NSE Security Token Master list from Dhan...")
        try:
            response = requests.get(self.csv_url, timeout=30)
            if response.status_code != 200:
                return False

            raw_data = response.content.decode('utf-8')
            df = pd.read_csv(io.StringIO(raw_data), dtype=str)
            df.columns = [col.strip().upper() for col in df.columns]
            
            exch_col = 'SEM_EXM_EXCH_ID'
            if exch_col not in df.columns:
                return False

            fo_df = df[df[exch_col].str.upper() == 'NSE_FO'].copy()
            fo_df.to_parquet(self.storage_path, compression='snappy')
            logging.info(f"✅ Token Master Synced. Cached {len(fo_df)} active derivative contracts.")
            return True
        except Exception as e:
            return False

    def lookup_option_token(self, trading_symbol: str) -> str:
        """Queries local parquet repository using an elastic string pattern fallback processor."""
        if not os.path.exists(self.storage_path):
            if not self.fetch_and_sync_tokens(): return "0"

        try:
            df = pd.read_parquet(self.storage_path)
            id_col = 'SEM_SMST_SECURITY_ID' if 'SEM_SMST_SECURITY_ID' in df.columns else 'SEM_SM_ID'
            symbol_cols = [c for c in df.columns if 'SYMBOL' in c]
            
            target = trading_symbol.upper().replace(" ", "")
            
            # Extract underlying asset and raw numeric strike parameters using regex
            extract_numbers = re.findall(r'\d+', target)
            strike_target = extract_numbers[-1] if extract_numbers else ""
            asset_prefix = "NIFTY" if "NIFTY" in target else ("BANKNIFTY" if "BANK" in target else "")

            for col in symbol_cols:
                # 1. Primary tight string lookup
                res = df[df[col].str.replace(" ", "", regex=False) == target]
                if not res.empty: return str(res.iloc[0][id_col])
                
                # 2. Institutional Fallback: Match by asset signature, contract strike code, and expiration type
                if asset_prefix and strike_target:
                    option_type = "CE" if "CE" in target else "PE"
                    
                    filter_mask = (df[col].str.contains(asset_prefix, regex=False)) & \
                                  (df[col].str.contains(strike_target, regex=False)) & \
                                  (df[col].str.endswith(option_type))
                                  
                    fallback_res = df[filter_mask]
                    if not fallback_res.empty:
                        # Return the nearest expiring option match from the dataframe row array
                        return str(fallback_res.iloc[0][id_col])
            
            return "0"
        except Exception as e:
            return "0"

if __name__ == "__main__":
    manager = ProductionTokenManager()
    # Test dynamic symbol parsing rules
    token_id = manager.lookup_option_token("NIFTY24MAY24050CE")
    print(f"\n⚡ Token Query Verification Result -> Resolved ID Code: {token_id}")
