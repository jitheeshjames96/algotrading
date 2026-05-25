import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

class SMCEngine:
    @staticmethod
    def apply_macro_trend(df: pd.DataFrame, ema_period: int = 200) -> pd.DataFrame:
        """Calculates a high-performance EMA to act as a strict macro filter."""
        df = df.copy()
        df['ema_200'] = df['close'].ewm(span=ema_period, adjust=False).mean()
        return df

    @staticmethod
    def detect_fvg(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['bullish_fvg'] = df['low'] > df['high'].shift(2)
        df['bearish_fvg'] = df['high'] < df['low'].shift(2)
        df['bullish_fvg_top'] = np.where(df['bullish_fvg'], df['low'], np.nan)
        df['bullish_fvg_bottom'] = np.where(df['bullish_fvg'], df['high'].shift(2), np.nan)
        return df

    @staticmethod
    def detect_structure(df: pd.DataFrame, window: int = 2) -> pd.DataFrame:
        df = df.copy()
        c = window 
        
        is_sh = (df['high'].shift(c) > df['high'].shift(c+1)) & (df['high'].shift(c) > df['high'].shift(c+2)) & \
                (df['high'].shift(c) > df['high'].shift(c-1)) & (df['high'].shift(c) > df['high'])
        
        is_sl = (df['low'].shift(c) < df['low'].shift(c+1)) & (df['low'].shift(c) < df['low'].shift(c+2)) & \
                (df['low'].shift(c) < df['low'].shift(c-1)) & (df['low'].shift(c) < df['low'])
                
        df['swing_high_price'] = np.where(is_sh, df['high'].shift(c), np.nan)
        df['swing_low_price'] = np.where(is_sl, df['low'].shift(c), np.nan)
        df['recent_swing_high'] = df['swing_high_price'].ffill()
        df['recent_swing_low'] = df['swing_low_price'].ffill()
        
        df['bullish_bos'] = (df['close'] > df['recent_swing_high']) & (df['close'].shift(1) <= df['recent_swing_high'].shift(1))
        df['bearish_bos'] = (df['close'] < df['recent_swing_low']) & (df['close'].shift(1) >= df['recent_swing_low'].shift(1))
        
        df['market_trend'] = np.where(df['bullish_bos'], 1, np.where(df['bearish_bos'], -1, np.nan))
        df['market_trend'] = df['market_trend'].ffill().fillna(0)
        return df

    @staticmethod
    def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
        """Combines SMC concepts WITH the Macro EMA Filter."""
        df = df.copy()
        df['active_bullish_fvg_top'] = df['bullish_fvg_top'].ffill()
        df['active_bullish_fvg_bottom'] = df['bullish_fvg_bottom'].ffill()
        
        # STRICT ARCHITECT RULE: Only buy if above 200 EMA
        df['long_signal'] = (df['market_trend'] == 1) & \
                            (df['low'] <= df['active_bullish_fvg_top']) & \
                            (df['close'] >= df['active_bullish_fvg_bottom']) & \
                            (df['close'] > df['ema_200']) # <-- The Buffett Filter
                            
        return df
