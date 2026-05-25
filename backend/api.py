from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
import uvicorn
import pandas as pd
from execution.database_manager import SupabaseDatabaseManager
from data.historical_feed import fetch_nse_data
from strategies.smc import SMCEngine

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

db = SupabaseDatabaseManager()

@app.get("/api/chart-data")
def get_chart_data():
    df = fetch_nse_data(ticker="^NSEI", interval="15m", period="59d")
    if df is None or df.empty:
        return {"error": "Failed to fetch data"}
        
    df.reset_index(drop=True, inplace=True)
    smc = SMCEngine()
    
    df = smc.apply_macro_trend(df, ema_period=50)
    df = smc.detect_fvg(df)
    df = smc.detect_structure(df)
    df = smc.generate_signals(df)
    
    df = df.dropna(subset=['timestamp'])
    
    chart_data = []
    for index, row in df.iterrows():
        ema_val = float(row['ema']) if 'ema' in row and not pd.isna(row['ema']) else None
        fvg_top = float(row['active_bullish_fvg_top']) if not pd.isna(row['active_bullish_fvg_top']) else None
        fvg_bottom = float(row['active_bullish_fvg_bottom']) if not pd.isna(row['active_bullish_fvg_bottom']) else None
        
        chart_data.append({
            "time": int(row['timestamp'].timestamp()),
            "open": float(row['open']),
            "high": float(row['high']),
            "low": float(row['low']),
            "close": float(row['close']),
            "long_signal": bool(row['long_signal']),
            "ema": ema_val,
            "fvg_top": fvg_top,
            "fvg_bottom": fvg_bottom
        })
        
    return {"candles": chart_data}

@app.get("/api/live-state")
def get_live_state():
    """Fetches production audit paths and telemetry states straight from Supabase."""
    if not db.client:
        return {"metrics": {}, "logs": []}
        
    try:
        # Fetch live analytics snapshot summary
        metrics_res = db.client.table("metrics_snapshot").select("*").eq("id", 1).execute()
        metrics = metrics_res.data[0] if metrics_res.data else {}
        
        # Fetch the last 10 algorithmic activity tracking trail logs ordered from newest to oldest
        logs_res = db.client.table("execution_logs").select("*").order("timestamp", desc=True).limit(10).execute()
        logs = logs_res.data if logs_res.data else []
        
        return {
            "metrics": {
                "capital": metrics.get("account_capital", 100000.00),
                "winRate": metrics.get("win_rate", 0.00),
                "netProfit": metrics.get("net_profit", 0.00),
                "activeTrades": metrics.get("active_allocations", 0),
                "safetyStatus": metrics.get("safety_state", "UNKNOWN")
            },
            "logs": [
                {
                    "timestamp": log.get("timestamp"),
                    "price": log.get("asset_price", 0.0),
                    "signal": log.get("metric_state", "SCANNING"),
                    "contract": log.get("contract_targeted"),
                    "details": log.get("action_details", "")
                } for log in logs
            ]
        }
    except Exception as e:
        print(f"API Fetch Error: {str(e)}")
        return {"metrics": {}, "logs": []}

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
