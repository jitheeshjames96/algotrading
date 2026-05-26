import os
import logging
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

from fyers_apiv3 import fyersModel
from fyers_apiv3.FyersWebsocket import data_ws
from strategies.smc import SMCEngine
from execution.mock_order_manager import MockExecutionManager
from execution.database_manager import SupabaseDatabaseManager

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

class LiveProductionTickEngine:
    def __init__(self, asset_symbol: str, fyers_symbol: str):
        self.symbol = asset_symbol
        self.fyers_symbol = fyers_symbol
        
        self.client_id = os.getenv("FYERS_CLIENT_ID", "").strip()
        self.access_token = os.getenv("FYERS_ACCESS_TOKEN", "").strip()
        if ":" in self.access_token: self.access_token = self.access_token.split(":")[-1]
        if not self.client_id.endswith("-100"): self.client_id = f"{self.client_id}-100"
            
        self.smc = SMCEngine()
        self.execution = MockExecutionManager()
        self.db = SupabaseDatabaseManager()
        
        self.tick_buffer = []          
        self.historical_candles = []   
        self.current_minute_block = -1 
        
        self.active_trade = False
        self.trade_direction = None    
        self.entry_price = 0.0
        self.current_sl = 0.0
        self.current_tp = 0.0
        self.lot_size = 25
        self.atm_delta = 0.50          

    def preload_historical_data(self):
        logging.info("⏳ [PRE-LOADER] Fetching historical market data...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=4)
        
        data = {
            "symbol": self.fyers_symbol,
            "resolution": "15",
            "date_format": "1",
            "range_from": start_date.strftime('%Y-%m-%d'),
            "range_to": end_date.strftime('%Y-%m-%d'),
            "cont_flag": "1"
        }
        
        try:
            fyers_api = fyersModel.FyersModel(client_id=self.client_id, token=self.access_token, is_async=False, log_path="")
            response = fyers_api.history(data=data)
            if response['s'] == 'ok':
                for c in response['candles']:
                    self.historical_candles.append({
                        "timestamp": datetime.fromtimestamp(c[0]),
                        "open": c[1], "high": c[2], "low": c[3], "close": c[4], "volume": c[5]
                    })
                logging.info(f"✅ [PRE-LOADER] Injected {len(response['candles'])} candles. 50 EMA Primed.")
            else:
                logging.error(f"❌ [PRE-LOADER] Failed: {response.get('message')}")
        except Exception as e:
            logging.critical(f"Pre-Loader Exception: {str(e)}")

    def calculate_unrealized_pnl(self, live_price: float):
        if not self.active_trade: return
        point_diff = live_price - self.entry_price if self.trade_direction == "BUY" else self.entry_price - live_price
        real_cash_pnl = (point_diff * self.atm_delta) * self.lot_size
        
        if len(self.tick_buffer) % 50 == 0:
            logging.info(f"💸 [MTM PnL] | Active Position: ₹{real_cash_pnl:.2f}")
            # Insert self.db.update_dashboard_pnl(real_cash_pnl) here

    def manage_open_position(self, live_price: float):
        self.calculate_unrealized_pnl(live_price)
        if (self.trade_direction == "BUY" and live_price <= self.current_sl) or (self.trade_direction == "SELL" and live_price >= self.current_sl):
            logging.warning(f"🛑 [STOP LOSS HIT] at ₹{live_price}. Flattening position.")
            self.active_trade = False
        elif (self.trade_direction == "BUY" and live_price >= self.current_tp) or (self.trade_direction == "SELL" and live_price <= self.current_tp):
            logging.info(f"💰 [TAKE PROFIT HIT] at ₹{live_price}. Securing gains.")
            self.active_trade = False

    def build_and_analyze_candle(self):
        if not self.tick_buffer: return
        df = pd.DataFrame(self.tick_buffer)
        candle = {
            "timestamp": df['timestamp'].iloc[-1],
            "open": df['price'].iloc[0], "high": df['price'].max(),
            "low": df['price'].min(), "close": df['price'].iloc[-1], "volume": len(df)
        }
        self.historical_candles.append(candle)
        logging.info(f"📊 [CANDLE CLOSED] | Close: ₹{candle['close']:.2f}")
        
        if len(self.historical_candles) >= 50:
            signal = "BUY" # Replace with actual SMC logic output
            metadata = {"fvg_top": candle['close']+15, "fvg_bottom": candle['close']-5, "ema": candle['close']-2}
            
            if signal:
                risk = 20.0
                sl_price = candle['close'] - risk if signal == "BUY" else candle['close'] + risk
                tp_price = candle['close'] + (risk * 2.0) if signal == "BUY" else candle['close'] - (risk * 2.0)
                
                self.execution.execute_paper_trade(candle['close'], signal, sl_price, tp_price, metadata)
                self.active_trade = True
                self.trade_direction = signal
                self.entry_price = candle['close']
                self.current_sl = sl_price
                self.current_tp = tp_price

    def process_live_tick(self, live_price: float, timestamp: datetime):
        if self.active_trade:
            self.manage_open_position(live_price)
            self.tick_buffer.append({'timestamp': timestamp, 'price': live_price})
            return

        current_block = timestamp.minute // 15 
        if self.current_minute_block == -1: self.current_minute_block = current_block 
            
        if current_block != self.current_minute_block:
            self.build_and_analyze_candle()
            self.tick_buffer = [] 
            self.current_minute_block = current_block
            
        self.tick_buffer.append({'timestamp': timestamp, 'price': live_price})

    def on_message(self, message):
        try:
            if isinstance(message, dict) and 'ltp' in message:
                live_price = float(message['ltp'])
                timestamp = datetime.fromtimestamp(message['exch_feed_time']) if 'exch_feed_time' in message else datetime.now()
                self.process_live_tick(live_price, timestamp)
        except Exception as e: logging.error(f"Tick Error: {str(e)}")

    def on_open(self):
        logging.info(f"✅ DataSocket Connected. Subscribing to {self.fyers_symbol}...")
        self.fyers_ws.subscribe(symbols=[self.fyers_symbol], data_type="SymbolUpdate")
        self.fyers_ws.keep_running()

    def on_error(self, message): pass
    def on_close(self, message): pass

    def start_live_stream(self):
        self.preload_historical_data()
        logging.info("🔌 Initializing BIFROST Production Engine...")
        ws_token = f"{self.client_id}:{self.access_token}"
        try:
            self.fyers_ws = data_ws.FyersDataSocket(
                access_token=ws_token, log_path="", litemode=False, write_to_file=False,
                reconnect=True, on_connect=self.on_open, on_close=self.on_close,
                on_error=self.on_error, on_message=self.on_message
            )
            self.fyers_ws.connect()
        except Exception as e: logging.critical(f"Failed WS Init: {str(e)}")

if __name__ == "__main__":
    engine = LiveProductionTickEngine("NIFTY 50", "NSE:NIFTY50-INDEX")
    engine.start_live_stream()
