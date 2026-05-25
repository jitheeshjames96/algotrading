import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

class OptionsRouter:
    def __init__(self):
        # Step values for Indian Indices
        self.step_values = {
            "NIFTY": 50,
            "BANKNIFTY": 100,
            "FINNIFTY": 50
        }

    def calculate_atm_strike(self, symbol: str, spot_price: float) -> int:
        """
        Calculates the At-The-Money (ATM) strike price based on the current spot price.
        """
        step = self.step_values.get(symbol.upper())
        if not step:
            raise ValueError(f"Unknown symbol: {symbol}. Cannot calculate strike step.")

        # Mathematical rounding to the nearest step value
        # Example: Nifty at 22634 / 50 = 452.68 -> rounds to 453 -> 453 * 50 = 22650
        atm_strike = round(spot_price / step) * step
        return atm_strike

    def generate_option_symbol(self, index: str, spot_price: float, signal_type: str, expiry_str: str) -> str:
        """
        Generates the standard Option Symbol (e.g., NIFTY24MAY22650CE)
        signal_type: 'LONG' = CE (Call Option), 'SHORT' = PE (Put Option)
        """
        atm_strike = self.calculate_atm_strike(index, spot_price)
        
        option_type = "CE" if signal_type.upper() == "LONG" else "PE"
        
        # Format: INDEX + EXPIRY + STRIKE + TYPE
        contract_symbol = f"{index.upper()}{expiry_str}{atm_strike}{option_type}"
        
        return contract_symbol

if __name__ == "__main__":
    router = OptionsRouter()
    
    # Let's simulate a Long Signal coming from your SMC Engine
    current_nifty_price = 22634.45
    signal = "LONG"
    expiry = "24MAY" # Dummy expiry format
    
    target_contract = router.generate_option_symbol("NIFTY", current_nifty_price, signal, expiry)
    
    logging.info("--- Options Router Test ---")
    logging.info(f"Nifty Spot Price: {current_nifty_price}")
    logging.info(f"SMC Signal: {signal} (Trend is Up, tapped into FVG)")
    logging.info(f"Executing Trade On: {target_contract}")
