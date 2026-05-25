import logging
import time
import pandas as pd  # <-- Added missing import
from data.historical_feed import fetch_nse_data
from strategies.smc import SMCEngine
from execution.router import OptionsRouter
from execution.risk_manager import RiskManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TradingBot:
    def __init__(self):
        self.smc = SMCEngine()
        self.router = OptionsRouter()
        self.risk_manager = RiskManager(account_balance=100000.0, risk_per_trade_pct=0.02)
        
    def run_cycle(self):
        logging.info("--- Starting Trading Cycle ---")
        
        df = fetch_nse_data(ticker="^NSEI", interval="15m", period="5d")
        if df is None or df.empty:
            logging.error("Failed to fetch market data. Aborting cycle.")
            return

        df = self.smc.detect_fvg(df)
        df = self.smc.detect_structure(df)
        df = self.smc.generate_signals(df)
        
        latest_candle = df.iloc[-1]
        current_price = latest_candle['close']
        
        logging.info(f"Nifty 50 Current Price: {current_price}")
        logging.info(f"Market Trend (1=Bullish, -1=Bearish): {latest_candle['market_trend']}")
        
        if latest_candle['long_signal']:
            logging.info("🚨 LONG SIGNAL DETECTED: Bullish Trend + Tapped into FVG!")
            
            expiry = "24MAY"
            contract = self.router.generate_option_symbol("NIFTY", current_price, "LONG", expiry)
            logging.info(f"🎯 Target Contract Generated: {contract}")
            
            recent_low = latest_candle['recent_swing_low']
            recent_high = latest_candle['recent_swing_high']
            
            if pd.isna(recent_low) or recent_low >= current_price:
                 recent_low = current_price - 30
            if pd.isna(recent_high) or recent_high <= current_price:
                 recent_high = current_price + 60
                 
            trade_plan = self.risk_manager.calculate_trade_parameters(
                entry_price=current_price,
                swing_low=recent_low,
                swing_high=recent_high
            )
            
            logging.info(f"🛡️ Risk Plan: Stop Loss @ {trade_plan['stop_loss']} | Take Profit @ {trade_plan['take_profit']}")
            
            if trade_plan['risk_reward_ratio'] >= 1.5:
                logging.info(f"✅ Executing Trade on {contract}...")
            else:
                logging.warning(f"⚠️ Trade Rejected. Risk/Reward {trade_plan['risk_reward_ratio']} is below 1.5 threshold.")
                
        else:
            logging.info("⏳ No valid setup detected. Waiting for next candle...")

if __name__ == "__main__":
    bot = TradingBot()
    bot.run_cycle()
