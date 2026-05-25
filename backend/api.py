from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import sys
import os
import uvicorn
import json
import asyncio
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from data.historical_feed import fetch_nse_data
from strategies.smc import SMCEngine

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Backend Client for API read operations
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key) if supabase_url and supabase_key else None

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
    """Queries the fresh real-time engine snapshots and execution data from Supabase."""
    if not supabase:
        return {"error": "Supabase client not initialized"}
        
    try:
        # Fetch snapshot statistics row
        metrics_res = supabase.table("metrics_snapshot").select("*").eq("id", 1).execute()
        # Fetch trailing 10 audit execution logs sorted by latest time
        logs_res = supabase.table("execution_logs").select("*").order("timestamp", desc=True).limit(10).execute()
        
        return {
            "metrics": metrics_res.data[0] if metrics_res.data else {},
            "logs": logs_res.data if logs_res.data else []
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
