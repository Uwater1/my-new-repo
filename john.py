import numpy as np
import pandas as pd
import pandas_ta as ta
import sys
from backtesting import Backtest, Strategy
from backtesting.lib import crossover

# ========================================
# 1. Data Loading & Preprocessing
# ========================================

def load_data(filepath):
    """
    Load and preprocess OHLCV data from CSV file.
    Expects columns: 'time', 'open', 'high', 'low', 'close', 'volume'
    """
    try:
        df = pd.read_csv(filepath)
        # Standardize column names
        df.columns = [x.lower() for x in df.columns]
        
        # Parse Time
        if 'time' in df.columns:
            df['time'] = pd.to_datetime(df['time'], utc=True)
            df.set_index('time', inplace=True)
        
        # Map to Backtesting.py required Capitalized columns
        df.rename(columns={
            'open': 'Open', 
            'high': 'High', 
            'low': 'Low', 
            'close': 'Close', 
            'volume': 'Volume'
        }, inplace=True)
        
        # Ensure floats and clean data
        cols = ['Open', 'High', 'Low', 'Close']
        df[cols] = df[cols].astype(float)
        df = df[~df.index.duplicated(keep='first')]
        df.sort_index(inplace=True)
        
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        # Return a dummy dataframe for demonstration if file fails
        print("Generating dummy data for demonstration...")
        dates = pd.date_range(start='2023-01-01', periods=1000, freq='5T')
        data = pd.DataFrame(index=dates)
        data['Open'] = 100 + np.cumsum(np.random.randn(1000))
        data['High'] = data['Open'] + 2
        data['Low'] = data['Open'] - 2
        data['Close'] = data['Open'] + np.random.randn(1000)
        return data

# ========================================
# 2. Helper Functions (The Logic Translation)
# ========================================

def get_stoch_k(high, low, close, k, d, smooth_k=1):
    """
    Wrapper to get just the %K line from pandas_ta Stoch function.
    John's strategy focuses heavily on the K line crossing/diverging.
    """
    # pandas_ta returns a DF with STOCHk and STOCHd columns
    stoch_df = ta.stoch(high, low, close, k=k, d=d, smooth_k=smooth_k)
    # Column names are usually STOCHk_... and STOCHd_...
    # We return the first column (%K)
    return stoch_df.iloc[:, 0]

def get_stoch_d(high, low, close, k, d, smooth_k=1):
    """Wrapper to get just the %D line"""
    stoch_df = ta.stoch(high, low, close, k=k, d=d, smooth_k=smooth_k)
    return stoch_df.iloc[:, 1]

# ========================================
# 3. The Strategy Class
# ========================================

class JohnKuriskoScalp(Strategy):
    # --- Parameters from Essay/Video ---
    # Fast (Trigger): 9, 3 [cite: 31, 84]
    stoch1_k = 9
    stoch1_d = 3
    
    # Standard: 14, 3 [cite: 33, 85]
    stoch2_k = 14
    stoch2_d = 3
    
    # Medium: 40, 4 (Essay) vs 44 (Video). Using Essay [cite: 86]
    stoch3_k = 40
    stoch3_d = 4
    
    # Slow (Trend): 60, 10, 10 (Full) [cite: 87]
    stoch4_k = 60
    stoch4_d = 10
    
    # Risk Management
    stop_loss_buffer = 1.0  # Points/dollars under the low
    take_profit_target = 0  # 0 = Dynamic exit based on Stoch

    def init(self):
        """
        Calculate all indicators before the loop starts for efficiency.
        """
        # 1. 200 EMA for Major Support/Resistance [cite: 90]
        self.ema200 = self.I(ta.ema, self.pd_data['Close'], length=200)
        
        # 2. The Four Stochastics (Quad Rotation components)
        # Note: We use self.pd_data to access the full pandas series for ta-lib
        h, l, c = self.pd_data['High'], self.pd_data['Low'], self.pd_data['Close']
        
        # 9-3-1 (Fastest)
        self.s9_k = self.I(get_stoch_k, h, l, c, self.stoch1_k, self.stoch1_d)
        
        # 14-3-1
        self.s14_k = self.I(get_stoch_k, h, l, c, self.stoch2_k, self.stoch2_d)
        
        # 40-4-1
        self.s40_k = self.I(get_stoch_k, h, l, c, self.stoch3_k, self.stoch3_d)
        
        # 60-10-10 (Full Stoch) - Note: pandas_ta stoch handles smoothing
        self.s60_k = self.I(get_stoch_k, h, l, c, self.stoch4_k, self.stoch4_d, smooth_k=10)

        # 3. Body Calculation for Divergence [cite: 46]
        # We need "Body Low" (min of Open/Close) and "Body High" (max of Open/Close)
        # We can calculate these on the fly in `next` or pre-calc here if needed.

    def next(self):
        """
        Executed for every candle. Here we check for:
        1. Quad Rotation (Environment)
        2. Divergence (Trigger)
        3. Exits
        """
        
        # --- A. DEFINE THE ENVIRONMENT (Quad Rotation) ---
        # "Trading Environment": All four stochastics aligned [cite: 40]
        # We use a slightly lenient threshold (e.g., < 25) for the "Quad" to ensure we don't miss 
        # setups where one stoch is slightly lagging.
        
        oversold_zone = 20
        overbought_zone = 80
        
        # Check Long Environment: Are we "Oversold"?
        quad_oversold = (self.s9_k[-1] < oversold_zone and 
                         self.s14_k[-1] < oversold_zone and 
                         self.s40_k[-1] < oversold_zone and 
                         self.s60_k[-1] < 30) # 60 is slower, give it breathing room

        # --- B. DIVERGENCE DETECTION (The Trigger) ---
        # Logic: Look for Price Lower Low + Stoch (9,3) Higher Low [cite: 45]
        
        long_signal = False
        
        # We need at least 10 bars of history to compare pivots
        if len(self.data) > 10:
            # 1. Identify "Current Pivot" (Candidate)
            # Current candle low is lower than previous 2 candles (simple pivot check)
            # Using BODY lows as per video instruction [cite: 46]
            curr_body_low = min(self.data.Open[-1], self.data.Close[-1])
            prev_body_low = min(self.data.Open[-2], self.data.Close[-2])
            
            # Simple Pivot: We just bounced up? (Green candle after Red)
            is_turning_up = self.data.Close[-1] > self.data.Open[-1]
            
            if quad_oversold and is_turning_up:
                # 2. Scan back 5-15 bars for a "Previous Pivot" that was LOWER on Stoch but HIGHER on Price
                # This is the "Bullish Divergence"
                
                # Current Stoch Value
                curr_stoch = self.s9_k[-1]
                
                # Look back window
                for i in range(2, 15):
                    past_body_low = min(self.data.Open[-i], self.data.Close[-i])
                    past_stoch = self.s9_k[-i]
                    
                    # Divergence Logic:
                    # Past Price was HIGHER than Current Price (Price made Lower Low)
                    # Past Stoch was LOWER than Current Stoch (Momentum made Higher Low)
                    price_lower_low = curr_body_low < past_body_low
                    stoch_higher_low = curr_stoch > past_stoch
                    
                    # Filter: The past stoch must have been deep oversold (<20) to count as a valid pivot
                    valid_pivot = past_stoch < 20
                    
                    if price_lower_low and stoch_higher_low and valid_pivot:
                        long_signal = True
                        break

        # --- C. EXECUTION LOGIC ---
        
        # 1. Entry
        if long_signal and not self.position:
            # Stop Loss: Under the lows of the entry candle [cite: 51]
            # We add a small buffer so we don't get stopped by noise
            sl_price = self.data.Low[-1] * 0.999 # 0.1% buffer
            
            # Size: Backtesting.py handles size via `cash` param, but we assume full equity here
            self.buy(sl=sl_price)

        # 2. Exit Strategy
        if self.position.is_long:
            # Rule 1: "Cash Out" Signal - 9-3 Stoch hits 80 
            time_to_exit = self.s9_k[-1] > 80
            
            # Rule 2: "Embedded" Exception - If 60-10 is > 80, HOLD 
            # This indicates a strong trend run (Bull Flag)
            is_embedded = self.s60_k[-1] > 80
            
            if time_to_exit and not is_embedded:
                self.position.close()
                
            # Note: We do not implement Short logic in this MVP to keep it focused on the video's primary examples
            # but the logic is simply the inverse.

    # Wrapper for pandas_ta access
    @property
    def pd_data(self):
        return pd.DataFrame({
            'Open': self.data.Open,
            'High': self.data.High,
            'Low': self.data.Low,
            'Close': self.data.Close,
            'Volume': self.data.Volume
        }, index=self.data.index)


# ========================================
# 4. Main Execution Block
# ========================================

if __name__ == "__main__":
    # Settings
    if len(sys.argv) > 1:
        DATA_FILE = sys.argv[1]
    else:
        DATA_FILE = '5min_data.csv'  # Default fallback
    INITIAL_CASH = 10000
    COMMISSION = 0.0001 # Estimate for fees
    
    # 1. Load Data
    # Check if file exists, else use dummy data
    import os
    if os.path.exists(DATA_FILE):
        print(f"Loading {DATA_FILE}...")
        df = load_data(DATA_FILE)
    else:
        print(f"File {DATA_FILE} not found. Using generated data.")
        df = load_data('dummy') # triggers dummy generation

    # 2. Initialize Backtest
    bt = Backtest(
        df, 
        JohnKuriskoScalp, 
        cash=INITIAL_CASH, 
        commission=COMMISSION,
        exclusive_orders=True 
    )

    # 3. Run
    print("Running Backtest...")
    stats = bt.run()
    
    # 4. Output Results
    print("\n--- Backtest Results ---")
    print(stats)
    
    # 5. Plot (Optional - requires browser)
    try:
        bt.plot()
    except Exception as e:
        print("Plotting failed (usually due to environment). Check stats above.")
