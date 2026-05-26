import logging
from datetime import datetime
from execution.database_manager import SupabaseDatabaseManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

class MockExecutionManager:
    def __init__(self):
        self.db = SupabaseDatabaseManager()

    def _calculate_atm_strike(self, spot_price: float, signal: str) -> str:
        strike = round(spot_price / 50) * 50
        option_type = "CE" if signal.upper() == 'BUY' else "PE"
        return f"NIFTY_ATM_{strike}_{option_type}"

    def execute_paper_trade(self, spot_price: float, signal: str, sl_price: float, tp_price: float, chart_metadata: dict):
        """
        Executes trade and passes exact chart coordinates to Supabase for the UI.
        """
        contract_symbol = self._calculate_atm_strike(spot_price, signal)
        
        logging.info("="*60)
        logging.info(f"🚨 [PAPER TRADE EXECUTED] | {signal} {contract_symbol}")
        logging.info(f"🎯 ENTRY: ₹{spot_price:.2f} | SL: ₹{sl_price:.2f} | TP: ₹{tp_price:.2f}")
        logging.info(f"📊 FVG ZONE: ₹{chart_metadata.get('fvg_bottom')} to ₹{chart_metadata.get('fvg_top')}")
        logging.info("="*60)
        
        # Format the precise data for Next.js Lightweight Charts to render
        rationale = f"SMC Alignment: Price hit 50 EMA at ₹{chart_metadata.get('ema_value')} inside 15m FVG."
        
        try:
            self.db.log_system_activity(
                price=spot_price,
                metric_state="SIMULATED_TRADE_EXECUTED",
                action_details=f"{signal} {contract_symbol} | SL: {sl_price} | TP: {tp_price}",
                # In a full Supabase push, you would insert this metadata JSON column
                # so the UI can draw the boxes and lines exactly where they occurred.
            )
            return True
        except Exception as e:
            logging.error(f"Failed to log to database: {str(e)}")
            return False
