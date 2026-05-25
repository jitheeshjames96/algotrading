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

def run_comprehensive_regime_backtest():
    logging.info("==========================================================")
    logging.info("   📈 INITIALIZING BIFROST STRATEGY ENVIRONMENT MATRIX")
    logging.info("==========================================================\n")
    
    df = fetch_nse_data(ticker="^NSEI", interval="15m", period="59d")
    if df is None or df.empty:
        logging.error("Failed to extract baseline data matrices.")
        return
        
    df.reset_index(drop=True, inplace=True)
    smc = SMCEngine()
    rm = RiskManager(account_balance=100000.0, risk_per_trade_pct=0.02)
    
    df = smc.apply_macro_trend(df, ema_period=50)
    df = smc.calculate_atr(df, period=14)
    df = smc.detect_fvg(df)
    df = smc.detect_structure(df)
    df = smc.generate_signals(df)
    
    signals = df[df['long_signal'] == True]
    
    starting_balance = 100000.0
    current_balance = starting_balance
    risk_per_trade = starting_balance * 0.02
    
    regimes = {
        "STRONG_BULL_MOMENTUM": {"wins": 0, "losses": 0, "net_pnl": 0.0},
        "SIDEWAYS_RANGE_CHOP": {"wins": 0, "losses": 0, "net_pnl": 0.0},
        "BEARISH_COUNTER_TREND": {"wins": 0, "losses": 0, "net_pnl": 0.0}
    }
    
    total_approved = 0

    for idx in signals.index:
        row = df.iloc[idx]
        current_price = row['close']
        sl = row['recent_swing_low']
        tp = row['recent_swing_high']
        atr = row['atr']
        ema = row['ema']
        
        if pd.isna(sl) or sl >= current_price: sl = current_price - 30
        if pd.isna(tp) or tp <= current_price: tp = current_price + 60
        
        atr_buffer = (atr * 1.5) if not pd.isna(atr) else 20.0
        protected_sl = sl - atr_buffer
        
        risk_points = current_price - protected_sl
        mechanical_tp = current_price + (risk_points * 1.5)
        final_tp = max(tp, mechanical_tp) # FIXED: Removed code syntax corruption characters
        
        plan = rm.calculate_trade_parameters(current_price, protected_sl, final_tp)
        
        if plan['risk_reward_ratio'] >= 1.5:
            total_approved += 1
            reward_amount = risk_per_trade * plan['risk_reward_ratio']
            
            # Context classification math relative to 50 EMA trendline
            pct_distance = ((current_price - ema) / max(1.0, ema)) * 100
            if pct_distance > 0.60:
                regime_name = "STRONG_BULL_MOMENTUM"
            elif 0.0 < pct_distance <= 0.60:
                regime_name = "SIDEWAYS_RANGE_CHOP"
            else:
                regime_name = "BEARISH_COUNTER_TREND"
                
            future_candles = df.iloc[idx+1:]
            outcome = "OPEN"
            
            print(f"⚡ [TRADE ENTRY] | {row['timestamp']} | Entry: ₹{current_price:.2f}")
            print(f"   ├─ Market Regime Context : {regime_name} ({pct_distance:.2f}% above trendline)")
            print(f"   └─ Targets               : SL @ ₹{plan['stop_loss']:.2f} | TP @ ₹{plan['take_profit']:.2f} | R:R -> 1:{plan['risk_reward_ratio']}")
            
            for _, future_row in future_candles.iterrows():
                if future_row['low'] <= plan['stop_loss']:
                    outcome = "LOSS"
                    regimes[regime_name]["losses"] += 1
                    regimes[regime_name]["net_pnl"] -= risk_per_trade
                    current_balance -= risk_per_trade
                    break
                elif future_row['high'] >= plan['take_profit']:
                    outcome = "WIN"
                    regimes[regime_name]["wins"] += 1
                    regimes[regime_name]["net_pnl"] += reward_amount
                    current_balance += reward_amount
                    break
                    
            if outcome == "WIN":
                print(f"   🟢 [RESULT] -> Target Reached. Gross Return: +₹{reward_amount:,.2f}\n")
            elif outcome == "LOSS":
                print(f"   🔴 [RESULT] -> Risk Guard Hit. Loss Accrued: -₹{risk_per_trade:,.2f}\n")
            else:
                print("   (Position remained open past backtest parameters)\n")

    print("\n" + "="*60)
    print("             📋 COMBINED REGIME SCORE REPORT")
    print("="*60)
    for regime, metrics in regimes.items():
        sub_trades = metrics["wins"] + metrics["losses"]
        regime_wr = (metrics["wins"] / sub_trades * 100) if sub_trades > 0 else 0.0
        print(f"📊 Regime Category : {regime}")
        print(f"   Fills Configured: {sub_trades} | Profit Matrix: {metrics['wins']}W - {metrics['losses']}L")
        print(f"   Regime Win Rate : {regime_wr:.2f}%")
        print(f"   Net Capital Shift: ₹{metrics['net_pnl']:,.2f}")
        print("-" * 60)
        
    total_net = current_balance - starting_balance
    global_wr = (sum(m['wins'] for m in regimes.values()) / max(1, total_approved) * 100)
    print(f"🏆 OVERALL ENGINE WIN RATE  : {global_wr:.2f}%")
    print(f"💰 INITIAL BLOCK CAPITAL    : ₹{starting_balance:,.2f}")
    print(f"💳 FINAL RECONCILED CAPITAL : ₹{current_balance:,.2f}")
    print(f"📊 TOTAL NET RETURN METRIC  : ₹{total_net:,.2f}")
    print("="*60)

if __name__ == "__main__":
    run_comprehensive_regime_backtest()
