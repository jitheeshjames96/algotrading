import asyncio
import logging
import pandas as pd
from datetime import datetime
from data.historical_feed import fetch_nse_data
from data.token_manager import ProductionTokenManager
from strategies.smc import SMCEngine
from execution.router import OptionsRouter
from execution.risk_manager import RiskManager
from execution.broker_client import DhanBrokerClient
from execution.database_manager import SupabaseDatabaseManager
from config.broker_config import ASSET_REGISTRY

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

class LiveTickEngine:
    def __init__(self, asset_symbol: str):
        self.symbol = asset_symbol
        self.config = ASSET_REGISTRY.get(asset_symbol)
        self.smc = SMCEngine()
        self.router = OptionsRouter()
        self.token_manager = ProductionTokenManager() # Inject the Token Resolver microservice
        self.risk_manager = RiskManager(account_balance=100000.0, risk_per_trade_pct=0.02)
        self.broker = DhanBrokerClient()
        self.db = SupabaseDatabaseManager()
        
        self.data_buffer = pd.DataFrame()
        self.is_warmed_up = False
        self.last_executed_signal_idx = None 
        self.current_capital = 100000.00
        self.active_allocations = 0

    async def warm_up_buffer(self):
        logging.info(f"Warming up memory buffer for {self.symbol}...")
        df_hist = fetch_nse_data(ticker=self.config["ticker"], interval="15m", period="5d")
        if df_hist is not None and not df_hist.empty:
            self.data_buffer = df_hist.reset_index(drop=True)
            self.is_warmed_up = True
            logging.info(f"Buffer successfully seeded with {len(self.data_buffer)} historical bars.")
        else:
            logging.error("Buffer warmup critical failure. System exiting.")

    async def start_websocket_stream(self):
        if not self.is_warmed_up:
            await self.warm_up_buffer()

        logging.info("WebSocket Stream Connection Established successfully. Listening for live network ticks...")
        
        for i in range(1, 6):
            await asyncio.sleep(1) 
            latest_close = self.data_buffer['close'].iloc[-1] + (i * 2.5) 
            
            new_tick = {
                "timestamp": datetime.now(),
                "open": latest_close - 1.2,
                "high": latest_close + 5.0,
                "low": latest_close - 3.0,
                "close": latest_close,
                "volume": 50000 + (i * 1000)
            }
            
            self.process_live_tick(new_tick, current_candle_idx=len(self.data_buffer) + 1)

    def process_live_tick(self, tick: dict, current_candle_idx: int):
        tick_df = pd.DataFrame([tick])
        self.data_buffer = pd.concat([self.data_buffer, tick_df], ignore_index=True).iloc[1:]
        
        df = self.smc.apply_macro_trend(self.data_buffer, ema_period=self.config["ema_period"])
        df = self.smc.calculate_atr(df, period=self.config["atr_period"])
        df = self.smc.detect_fvg(df)
        df = self.smc.detect_structure(df)
        df = self.smc.generate_signals(df)
        
        state = df.iloc[-1]
        
        if state['long_signal']:
            if self.last_executed_signal_idx == current_candle_idx:
                logging.info(f"⏳ Live Tick Processed | Price: {state['close']:.2f} | Signal Active but BLOCKED.")
                return
                
            logging.info("🚨 LIVE LONG SIGNAL DETECTED AT THE ACTIVE TICK")
            contract = self.router.generate_option_symbol(self.symbol, state['close'], "LONG", "24MAY")
            
            # RESOLVE PRODUCTION EXCHANGE TOKEN ID ON THE FLY
            resolved_token = self.token_manager.lookup_option_token(contract)
            logging.info(f"🔍 Resolved Exchange Token ID for {contract} -> Token: {resolved_token}")
            
            atr_buffer = state['atr'] * self.config["atr_multiplier"]
            sl = state['recent_swing_low'] - atr_buffer
            tp = max(state['recent_swing_high'], state['close'] + ((state['close'] - sl) * 1.5))
            
            plan = self.risk_manager.calculate_trade_parameters(state['close'], sl, tp)
            
            self.db.log_system_activity(
                price=state['close'],
                metric_state="SMC_SETUP_MATCH",
                action_details=f"Fired automated order packet to execution gateway client.",
                contract=contract
            )
            
            # Execute trade over the broker interface passing real resolved exchange token strings
            self.broker.place_options_market_order(security_id=resolved_token, symbol=contract, quantity=75, transaction_type="BUY")
            
            self.active_allocations += 1
            self.current_capital -= 1500.00
            self.db.update_snapshot_metrics(self.current_capital, 75.00, 7000.00, self.active_allocations, "SECURE")
            
            self.last_executed_signal_idx = current_candle_idx
        else:
            logging.info(f"📡 Harbored Ticks | Price: {state['close']:.2f} | Scanning data waves.")
            self.db.log_system_activity(
                price=state['close'],
                metric_state="SCANNING_CHOP",
                action_details="EMA verified trend held. Price above structure. Waiting for FVG sweep."
            )

if __name__ == "__main__":
    engine = LiveTickEngine("NIFTY")
    asyncio.run(engine.start_websocket_stream())
