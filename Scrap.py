import numpy as np
import pandas as pd
import pandas_ta as ta
import sys
from backtesting import Backtest, Strategy

# ========================================
# 1. Data Loading & Preprocessing
# ========================================

def load_data(filepath):
    """
    Loads generic 5-min CSV.
    Expected columns: Time, Open, High, Low, Close, Volume
    """
    try:
        df = pd.read_csv(filepath)
        df.columns = [x.lower() for x in df.columns]
        
        # Ensure DateTime Index
        if 'time' in df.columns:
            # Parse as UTC, then convert to Eastern Time
            df['time'] = pd.to_datetime(df['time'], utc=True)
            df['time'] = df['time'].dt.tz_convert('America/New_York')
            df.set_index('time', inplace=True)
            
        df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
        cols = ['Open', 'High', 'Low', 'Close']
        df[cols] = df[cols].astype(float)
        
        # Remove duplicates and sort
        df = df[~df.index.duplicated(keep='first')]
        df.sort_index(inplace=True)
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def add_strategy_indicators(df):
    """
    Pre-calculates Daily ATR and Opening Range (09:30-09:45) statistics.
    """
    df = df.copy()
    
    # Ensure we have a DatetimeIndex before proceeding
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("DataFrame index must be a DatetimeIndex. Check load_data function.")
    
    # Save the original DatetimeIndex before any merge operations
    original_index = df.index.copy()
    
    # --- 1. Calculate Daily ATR (14) ---
    # Resample to daily to get proper ATR
    daily_df = df.resample('D').agg({
        'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'
    }).dropna()
    
    # Calculate ATR using pandas_ta
    daily_df['ATR_14'] = ta.atr(daily_df['High'], daily_df['Low'], daily_df['Close'], length=14)
    
    # SHIFT ATR: We must use *yesterday's* ATR for *today's* calculation to avoid lookahead
    daily_df['Prev_Day_ATR'] = daily_df['ATR_14'].shift(1)
    
    # Map Daily ATR back to 5-min dataframe
    # We create a 'Date' column to merge on
    df['Date'] = df.index.date
    daily_df['Date'] = daily_df.index.date
    
    # Merge (Left join on Date)
    df = df.merge(daily_df[['Date', 'Prev_Day_ATR']], on='Date', how='left')
    # Restore the original DatetimeIndex after merge
    df.index = original_index

    # --- 2. Identify Opening Range (09:30 - 09:45) ---
    # We assume the index is datetime. Filter for the specific times.
    # Note: 09:30, 09:35, 09:40 are the three 5-min bars that make up the 15-min Open.
    
    # Create mask for OR bars
    # Adjust times if your CSV is in UTC (e.g. 13:30 for 9:30 ET)
    or_start = "09:30"
    or_end_candle_start = "09:40" # The candle starting at 9:40 ends at 9:45
    
    # Identify the specific bars
    df['Time_Str'] = df.index.strftime('%H:%M')
    mask_or = (df['Time_Str'] >= or_start) & (df['Time_Str'] <= or_end_candle_start)
    
    # Group by Date to calculate OR High/Low/Open/Close per day
    or_stats = df[mask_or].groupby('Date').agg(
        OR_High=('High', 'max'),
        OR_Low=('Low', 'min'),
        OR_Open=('Open', 'first'),
        OR_Close=('Close', 'last')
    )
    
    # Calculate OR Height
    or_stats['OR_Height'] = or_stats['OR_High'] - or_stats['OR_Low']
    
    # Determine Bias: 
    # Green OR (Close > Open) -> Manipulation Up -> Bias Short
    # Red OR (Close < Open) -> Manipulation Down -> Bias Long
    or_stats['OR_Direction'] = np.where(or_stats['OR_Close'] > or_stats['OR_Open'], 1, -1) # 1 = Green, -1 = Red
    
    # Map these stats back to the main dataframe using map (preserves index)
    for col in ['OR_High', 'OR_Low', 'OR_Height', 'OR_Direction']:
        mapper = or_stats[col].to_dict()
        df[col] = df['Date'].map(mapper)
        
    return df

# ========================================
# 2. Strategy Class
# ========================================

class PatternScalp(Strategy):
    # Optimization Parameters
    atr_threshold_pct = 0.20  # 20% of Daily ATR
    profit_target_ratio = 0.5 # 50% retracement of the range
    stop_buffer = 1.0         # 1 point buffer
    
    def init(self):
        # These columns are pre-calculated in add_strategy_indicators
        self.prev_atr = self.I(lambda x: x, self.data.Prev_Day_ATR)
        self.or_high = self.I(lambda x: x, self.data.OR_High)
        self.or_low = self.I(lambda x: x, self.data.OR_Low)
        self.or_height = self.I(lambda x: x, self.data.OR_Height)
        self.or_direction = self.I(lambda x: x, self.data.OR_Direction) # 1=Green(Look Short), -1=Red(Look Long)
        
        # Helper for time check
        self.time_str = self.data.df.index.strftime('%H:%M')

    def next(self):
        # 1. Trading Window Check
        # We only trade AFTER the OR is done (post 09:45)
        # We stop taking new trades after 11:00 (optional filter to avoid chop)
        current_time = self.time_str[-1]
        
        # Skip if before 09:45
        if current_time <= "09:40": 
            return
            
        # One trade per day logic (strict scalping)
        if len(self.trades) > 0:
            # Check if we already traded today. 
            # Note: self.trades includes active trades. self.closed_trades check might be needed for full strictness.
            # For simplicity, if we are in a trade, do nothing.
            
            # Close trade at 3:30 PM if still open
            if current_time >= "15:30":
                for trade in self.trades:
                    trade.close()
            return

        # 2. Manipulation Validation
        # Is the OR Height big enough?
        atr = self.prev_atr[-1]
        height = self.or_height[-1]
        threshold = atr * self.atr_threshold_pct
        
        if height < threshold:
            return # No manipulation, no trade
            
        # 3. Determine Setup Direction
        or_dir = self.or_direction[-1]
        
        # Setup: BIAS SHORT (OR was Green/Up)
        if or_dir == 1:
            # Look for Reversal Candle at/near OR High
            # Trigger: "John Wick" (Shooting Star) OR "Power Tower" (Bearish Engulfing)
            
            # Simple Wick Logic: Upper wick > Body
            open_p, close_p, high_p, low_p = self.data.Open[-1], self.data.Close[-1], self.data.High[-1], self.data.Low[-1]
            body_size = abs(close_p - open_p)
            upper_wick = high_p - max(open_p, close_p)
            
            # Condition A: Location (Must be near OR High)
            # Let's say High must be >= OR High - tiny buffer, or simply broke it
            if high_p >= self.or_high[-1]:
                
                # Condition B: Pattern
                is_shooting_star = (upper_wick > body_size * 1.5)
                is_bearish_engulfing = (close_p < open_p) and (close_p < self.data.Low[-2]) and (open_p > self.data.High[-2])
                
                if is_shooting_star or is_bearish_engulfing:
                    # ENTRY SHORT
                    # Entry at current close price
                    entry_price = close_p
                    # Stop loss above entry price (for short, SL must be > entry)
                    stop_loss = entry_price + self.stop_buffer
                    # Target: 50% of the range
                    # For short trade: TP < Entry < SL
                    # Ensure TP is below entry price
                    or_target = self.or_low[-1] + (height * 0.5)
                    take_profit = min(or_target, entry_price - 1.0)  # Ensure TP < entry
                    
                    self.sell(sl=stop_loss, tp=take_profit)

        # Setup: BIAS LONG (OR was Red/Down)
        elif or_dir == -1:
            # Look for Reversal Candle at/near OR Low
            open_p, close_p, high_p, low_p = self.data.Open[-1], self.data.Close[-1], self.data.High[-1], self.data.Low[-1]
            body_size = abs(close_p - open_p)
            lower_wick = min(open_p, close_p) - low_p
            
            # Condition A: Location (Must be near OR Low)
            if low_p <= self.or_low[-1]:
                
                # Condition B: Pattern
                is_hammer = (lower_wick > body_size * 1.5)
                is_bullish_engulfing = (close_p > open_p) and (close_p > self.data.High[-2]) and (open_p < self.data.Low[-2])
                
                if is_hammer or is_bullish_engulfing:
                    # ENTRY LONG
                    # Entry at current close price
                    entry_price = close_p
                    # Stop loss below entry price (for long, SL must be < entry)
                    stop_loss = entry_price - self.stop_buffer
                    # Target: 50% of the range above OR Low
                    # For long trade: SL < Entry < TP
                    # Ensure TP is above entry price
                    or_target = self.or_low[-1] + (height * 0.5)
                    take_profit = max(or_target, entry_price + 1.0)  # Ensure TP > entry
                    
                    self.buy(sl=stop_loss, tp=take_profit)

# ========================================
# 3. Execution & Optimization
# ========================================

def run_strategy(filepath, optimize=False):
    # 1. Load
    raw_df = load_data(filepath)
    if raw_df is None: return
    
    # 2. Preprocess
    processed_df = add_strategy_indicators(raw_df)
    
    # Check if we have data left (cleaning might remove some rows)
    processed_df.dropna(inplace=True)
    
    if processed_df.empty:
        print("Dataframe empty after preprocessing.")
        return

    # 3. Setup Backtest
    bt = Backtest(processed_df, PatternScalp, cash=100_000, commission=.0001, exclusive_orders=True)
    
    if optimize:
        print("Starting Optimization...")
        stats = bt.optimize(
            atr_threshold_pct=[0.15, 0.20, 0.25, 0.30],
            profit_target_ratio=[0.5, 0.8, 1.0],
            maximize='Return [%]',
            constraint=lambda param: param.profit_target_ratio > 0 # Example constraint
        )
        print("\n--- Optimized Stats ---")
        print(stats)
        print("\n--- Best Parameters ---")
        print(stats._strategy)
        
        bt.plot() # Uncomment to see plot in browser
    else:
        print("Running Single Backtest...")
        stats = bt.run()
        print(stats)
        bt.plot()

if __name__ == "__main__":
    # Check if command line argument is provided
    if len(sys.argv) != 2:
        print("Usage: python Scrap.py <csv_file_path>")
        print("Example: python Scrap.py Emini5min.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    run_strategy(csv_file, optimize=True)