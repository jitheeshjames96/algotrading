import logging
import sys
import os
import pandas as pd
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.historical_feed import fetch_nse_data
from strategies.smc import SMCEngine
from execution.risk_manager import RiskManager

logging.basicConfig(level=logging.INFO, format='%(message)s')

def run_pro_regime_backtest(ticker, config):
    df = fetch_nse_data(ticker=ticker, interval="15m", period="59d")
    if df is None or df.empty: return {"win_rate": 0, "pnl": 0}
    df.reset_index(drop=True, inplace=True)
    
    smc = SMCEngine()
    rm = RiskManager(account_balance=100000.0, risk_per_trade_pct=0.02)
    
    # Use dynamic config
    df = smc.apply_macro_trend(df, ema_period=config['ema'])
    df = smc.calculate_atr(df, period=14)
    df = smc.detect_fvg(df)
    df = smc.detect_structure(df)
    df = smc.generate_signals(df)
    
    signals = df[df['long_signal'] == True]
    starting_balance = 100000.0
    current_balance = starting_balance
    risk_per_trade = starting_balance * 0.02
    
    wins = losses = 0
    
    for idx in signals.index:
        row = df.iloc[idx]
        current_price = row['close']
        sl = row['recent_swing_low']
        tp = row['recent_swing_high']
        atr = row['atr']
        
        if pd.isna(sl) or sl >= current_price: sl = current_price - 30
        if pd.isna(tp) or tp <= current_price: tp = current_price + 60
        
        atr_buffer = (atr * config['atr_mul']) if not pd.isna(atr) else 20.0
        protected_sl = sl - atr_buffer
        
        risk_points = current_price - protected_sl
        mechanical_tp = current_price + (risk_points * 1.5)
        final_tp = max(tp, mechanical_tp)
        
        plan = rm.calculate_trade_parameters(current_price, protected_sl, final_tp)
        
        if plan['risk_reward_ratio'] >= 1.5:
            future_candles = df.iloc[idx+1:]
            for _, future_row in future_candles.iterrows():
                if future_row['low'] <= plan['stop_loss']:
                    losses += 1
                    current_balance -= risk_per_trade
                    break
                elif future_row['high'] >= plan['take_profit']:
                    wins += 1
                    current_balance += (risk_per_trade * plan['risk_reward_ratio'])
                    break
                    
    total = wins + losses
    return {
        "win_rate": (wins / total * 100) if total > 0 else 0,
        "pnl": current_balance - starting_balance
    }
