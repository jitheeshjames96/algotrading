import logging
import sys
import os
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.historical_feed import fetch_nse_data
from strategies.smc import SMCEngine
from execution.risk_manager import RiskManager

logging.basicConfig(level=logging.INFO, format='%(message)s')

def run_portfolio_backtest():
    logging.info("--- Initializing Multi-Asset Portfolio Engine ---")
    
    tickers = ["^NSEI", "^NSEBANK"] # Nifty 50 and BankNifty
    
    starting_balance = 100000.0
    current_balance = starting_balance
    risk_per_trade = starting_balance * 0.02
    
    total_wins = total_losses = total_break_evens = total_open = total_approved = 0
    
    smc = SMCEngine()
    rm = RiskManager(account_balance=starting_balance, risk_per_trade_pct=0.02)
    
    for ticker in tickers:
        logging.info(f"Scanning {ticker}...")
        df = fetch_nse_data(ticker=ticker, interval="15m", period="59d")
        if df is None or df.empty: 
            logging.warning(f"Skipping {ticker} due to data fetch failure.")
            continue
            
        df.reset_index(drop=True, inplace=True)
        
        df = smc.apply_macro_trend(df, ema_period=50)
        df = smc.calculate_atr(df, period=14)
        df = smc.detect_fvg(df)
        df = smc.detect_structure(df)
        df = smc.generate_signals(df)
        
        signals = df[df['long_signal'] == True]
        
        for idx in signals.index:
            row = df.iloc[idx]
            current_price = row['close']
            sl = row['recent_swing_low']
            tp = row['recent_swing_high']
            atr = row['atr']
            
            if pd.isna(sl) or sl >= current_price: sl = current_price - (current_price * 0.002)
            if pd.isna(tp) or tp <= current_price: tp = current_price + (current_price * 0.004)
            
            atr_buffer = (atr * 1.5) if not pd.isna(atr) else (current_price * 0.001)
            protected_sl = sl - atr_buffer
            
            risk_points = current_price - protected_sl
            mechanical_tp = current_price + (risk_points * 1.5)
            final_tp = max(tp, mechanical_tp)
            
            plan = rm.calculate_trade_parameters(current_price, protected_sl, final_tp)
            
            if plan['risk_reward_ratio'] >= 1.5:
                total_approved += 1
                trade_closed = False
                reward_amount = risk_per_trade * plan['risk_reward_ratio']
                future_candles = df.iloc[idx+1:]
                
                active_sl = plan['stop_loss']
                entry_price = plan['entry']
                break_even_triggered = False
                target_1r = entry_price + risk_points
                
                for _, future_row in future_candles.iterrows():
                    if not break_even_triggered and future_row['high'] >= target_1r:
                        active_sl = entry_price
                        break_even_triggered = True

                    if future_row['low'] <= active_sl:
                        if break_even_triggered:
                            total_break_evens += 1
                        else:
                            total_losses += 1
                            current_balance -= risk_per_trade
                        trade_closed = True
                        break
                        
                    elif future_row['high'] >= plan['take_profit']:
                        total_wins += 1
                        current_balance += reward_amount
                        trade_closed = True
                        break
                        
                if not trade_closed: total_open += 1

    total_closed_trades = total_wins + total_losses + total_break_evens
    win_rate = (total_wins / total_closed_trades * 100) if total_closed_trades > 0 else 0
    net_profit = current_balance - starting_balance

    print("\n" + "="*45)
    print(" 🌍 MULTI-ASSET PORTFOLIO BACKTEST REPORT")
    print("="*45)
    print(f"Indices Scanned       : {', '.join(tickers)}")
    print(f"Total Approved Trades : {total_approved}")
    print(f"Wins (Full Target)    : {total_wins}")
    print(f"Losses (Full Stop)    : {total_losses}")
    print(f"Break-Evens (Saved!)  : {total_break_evens}")
    print(f"Still Open            : {total_open}")
    print("-" * 45)
    print(f"Win Rate              : {win_rate:.2f}%")
    print(f"Ending Capital        : ₹{current_balance:,.2f}")
    print(f"Net Profit            : ₹{net_profit:,.2f}")
    print("="*45)

if __name__ == "__main__":
    run_portfolio_backtest()
