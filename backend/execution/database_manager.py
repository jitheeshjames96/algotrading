import os
import logging
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(message)s')

class SupabaseDatabaseManager:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        
        if not self.url or not self.key:
            logging.warning("⚠️ Supabase credentials missing from environmental runtime. Operating in local memory mode.")
            self.client = None
        else:
            # Initialize connection pool client
            self.client = create_client(self.url, self.key)
            logging.info("🔌 High-Performance Uplink connected to Supabase Cloud Engine.")

    def log_system_activity(self, price: float, metric_state: str, action_details: str, contract: str = None):
        """Dispatches an audit log row to the execution_logs table."""
        if not self.client:
            return
            
        payload = {
            "asset_price": float(price),
            "metric_state": str(metric_state),
            "action_details": str(action_details),
            "contract_targeted": str(contract) if contract else None
        }
        
        try:
            # Fire-and-forget vectorized insertion
            self.client.table("execution_logs").insert(payload).execute()
        except Exception as e:
            logging.error(f"❌ Failed to commit audit trail to Supabase: {str(e)}")

    def update_snapshot_metrics(self, capital: float, win_rate: float, net_profit: float, allocations: int, safety: str):
        """Updates the top-line dashboard metrics index row."""
        if not self.client:
            return
            
        payload = {
            "account_capital": float(capital),
            "win_rate": float(win_rate),
            "net_profit": float(net_profit),
            "active_allocations": int(allocations),
            "safety_state": str(safety)
        }
        
        try:
            # Update row ID 1 (our seeded bootstrap state row)
            self.client.table("metrics_snapshot").update(payload).eq("id", 1).execute()
        except Exception as e:
            logging.error(f"❌ Failed to sync metric snapshot to cloud: {str(e)}")

if __name__ == "__main__":
    db = SupabaseDatabaseManager()
    db.log_system_activity(24052.40, "SMC_SETUP_MATCH", "Simulated system diagnostic probe successful", "NIFTY24MAY24050CE")
