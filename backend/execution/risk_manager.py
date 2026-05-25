import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

class RiskManager:
    def __init__(self, account_balance: float, risk_per_trade_pct: float = 0.02):
        self.account_balance = account_balance
        self.risk_per_trade_pct = risk_per_trade_pct  # e.g., 0.02 = 2% risk

    def calculate_trade_parameters(self, entry_price: float, swing_low: float, swing_high: float):
        """
        Calculates Stop Loss (SL), Take Profit (TP), and the Risk/Reward ratio
        based on the underlying spot price (Nifty 50).
        """
        # SMC Stop Loss: Slightly below the recent swing low or FVG bottom
        # We subtract a tiny buffer (e.g., 2 points for Nifty) to avoid exact tick sweeps
        spot_sl = swing_low - 2.0 
        
        # SMC Take Profit: Target the recent swing high (Liquidity pool)
        spot_tp = swing_high
        
        risk_points = entry_price - spot_sl
        reward_points = spot_tp - entry_price
        
        # Avoid division by zero if prices are identical
        if risk_points <= 0:
            risk_points = 0.1
            
        rr_ratio = reward_points / risk_points
        
        return {
            "entry": entry_price,
            "stop_loss": spot_sl,
            "take_profit": spot_tp,
            "risk_reward_ratio": round(rr_ratio, 2),
            "max_monetary_risk": self.account_balance * self.risk_per_trade_pct
        }

if __name__ == "__main__":
    # Simulate an account with ₹1,00,000 capital
    rm = RiskManager(account_balance=100000.0, risk_per_trade_pct=0.02)
    
    # Simulated SMC Signal Data (Nifty 50)
    current_spot = 22634.00
    recent_low = 22610.00
    recent_high = 22700.00
    
    trade_plan = rm.calculate_trade_parameters(
        entry_price=current_spot, 
        swing_low=recent_low, 
        swing_high=recent_high
    )
    
    logging.info("--- SMC Risk & Trade Plan Generated ---")
    logging.info(f"Max Risk Allowed: ₹{trade_plan['max_monetary_risk']}")
    logging.info(f"Spot Entry: {trade_plan['entry']}")
    logging.info(f"Spot Stop Loss: {trade_plan['stop_loss']}")
    logging.info(f"Spot Take Profit: {trade_plan['take_profit']}")
    logging.info(f"Risk/Reward Ratio: 1 : {trade_plan['risk_reward_ratio']}")
    
    if trade_plan['risk_reward_ratio'] < 1.5:
        logging.warning("⚠️ Trade Skipped: Risk/Reward is below 1:1.5 threshold.")
    else:
        logging.info("✅ Trade Approved by Risk Manager.")
