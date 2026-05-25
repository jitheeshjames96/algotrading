import logging
import sys
import os
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.historical_feed import fetch_nse_data
from strategies.smc import SMCEngine
from execution.risk_manager import RiskManager

logging.basicConfig(level=logging.INFO, format='%(message)s')

def run_historical_backtest():
    logging.info("--- Initializing Precision P&L Backtester (Free Data Mode) ---")
    
    # Kept under the hard 60-day limit for Yahoo Finance 15m data
    df = fetch_nse_data(ticker="^NSEI", interval="15m", period="59d")
    
    if df is None or df.empty: return
    df.reset_index(drop=True, inplace=True)

    smc = SMCEngine()
    rm = RiskManager(account_balance=100000.0, risk_per_trade_pct=0.02)
    
    # Using a 50 EMA instead of 200 EMA so it warms up within our limited data
    df = smc.apply_macro_trend(df, ema_period=50)
    df = smc.detect_fvg(df)
    df = smc.detect_structure(df)
    df = smc.generate_signals(df)
    
    signals = df[df['long_signal'] == True]
    
    starting_balance = 100000.0
    current_balance = starting_balance
    risk_per_trade = starting_balance * 0.02
    
    wins = losses = open_trades = 0
    
    for idx in signals.index:
        row = df.iloc[idx]
        current_price = row['close']
        sl = row['recent_swing_low']
        tp = row['recent_swing_high']
        
        if pd.isna(sl) or sl >= current_price: sl = current_price - 30
        if pd.isna(tp) or tp <= current_price: tp = current_price + 60
        
        plan = rm.calculate_trade_parameters(current_price, sl, tp)
        
        if plan['risk_reward_ratio'] >= 1.5:
            trade_closed = False
            reward_amount = risk_per_trade * plan['risk_reward_ratio']
            future_candles = df.iloc[idx+1:]
            
            for _, future_row in future_candles.iterrows():
                if future_row['low'] <= plan['stop_loss']:
                    losses += 1
                    current_balance -= risk_per_trade
                    trade_closed = True
                    break
                elif future_row['high'] >= plan['take_profit']:
                    wins += 1
                    current_balance += reward_amount
                    trade_closed = True
                    break
            if not trade_closed: open_trades += 1

    total_closed_trades = wins + losses
    win_rate = (wins / total_closed_trades * 100) if total_closed_trades > 0 else 0
    net_profit = current_balance - starting_balance

    print("\n" + "="*40)
    print("      📊 PRECISION P&L BACKTEST REPORT")
    print("="*40)
    print(f"Total Approved Trades : {total_closed_trades + open_trades}")
    print(f"Wins                  : {wins}")
    print(f"Losses                : {losses}")
    print("-" * 40)
    print(f"Win Rate              : {win_rate:.2f}%")
    print(f"Ending Capital        : ₹{current_balance:,.2f}")
    print(f"Net Profit            : ₹{net_profit:,.2f}")
    print("="*40)

if __name__ == "__main__":
    run_historical_backtest()
