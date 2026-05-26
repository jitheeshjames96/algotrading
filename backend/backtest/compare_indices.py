import pandas as pd
from engine import run_pro_regime_backtest

# Define specific configuration per asset
assets = {
    "^NSEI": {"ema": 50, "atr_mul": 1.5},
    "^NSEBANK": {"ema": 20, "atr_mul": 2.2}
}

def compare_performance():
    print(f"\n{'INDEX':<15} | {'WIN RATE':<10} | {'NET P&L':<15}")
    print("-" * 45)
    for ticker, config in assets.items():
        # Pass the config to the engine to drive asset-specific math
        res = run_pro_regime_backtest(ticker, config)
        print(f"{ticker:<15} | {res['win_rate']:<10.2f}% | ₹{res['pnl']:,.2f}")

if __name__ == "__main__":
    compare_performance()
