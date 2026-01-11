import numpy as np
import pandas as pd
import pandas_ta as ta
import sys
from backtesting import Backtest, Strategy

# ========================================
# 1. Data Loading & Preprocessing
# ========================================

def load_data(filepath):
    try:
        df = pd.read_csv(filepath)
        df.columns = [x.lower() for x in df.columns]
        if 'time' in df.columns:
            df['time'] = pd.to_datetime(df['time'], utc=True)
            df.set_index('time', inplace=True)
        df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
        cols = ['Open', 'High', 'Low', 'Close']
        df[cols] = df[cols].astype(float)
        df = df[~df.index.duplicated(keep='first')]
        df.sort_index(inplace=True)
        return df
    except Exception as e:
        print(f"Error: {e}")
        return None

# ========================================
# 2. Helper Functions
# ========================================

def get_stoch_k(high, low, close, k, d, smooth_k=1):
    stoch_df = ta.stoch(high, low, close, k=k, d=d, smooth_k=smooth_k)
    return stoch_df.iloc[:, 0]

# ========================================
# 3. Refined Strategy Class
# ========================================

class JohnKuriskoScalp(Strategy):
    # Parameters
    stoch1_k, stoch1_d = 9, 3
    stoch2_k, stoch2_d = 14, 3
    stoch3_k, stoch3_d = 44, 4
    stoch4_k, stoch4_d = 60, 10
    
    ema_fast_len = 20
    ema_slow_len = 200

    def init(self):
        self.ema20 = self.I(ta.ema, pd.Series(self.data.Close), length=self.ema_fast_len)
        self.ema200 = self.I(ta.ema, pd.Series(self.data.Close), length=self.ema_slow_len)
        
        h, l, c = pd.Series(self.data.High), pd.Series(self.data.Low), pd.Series(self.data.Close)
        self.s9_k = self.I(get_stoch_k, h, l, c, self.stoch1_k, self.stoch1_d)
        self.s14_k = self.I(get_stoch_k, h, l, c, self.stoch2_k, self.stoch2_d)
        self.s44_k = self.I(get_stoch_k, h, l, c, self.stoch3_k, self.stoch3_d)
        self.s60_k = self.I(get_stoch_k, h, l, c, self.stoch4_k, self.stoch4_d, smooth_k=10)

        self.body_low = self.I(lambda o, c: np.minimum(o, c), self.data.Open, self.data.Close)
        self.body_high = self.I(lambda o, c: np.maximum(o, c), self.data.Open, self.data.Close)

    def find_pivot(self, series, type='low', window=15):
        if len(series) < window + 2: return None, None
        sub = series[-window:]
        val = np.min(sub) if type == 'low' else np.max(sub)
        idx = np.where(sub == val)[0][-1]
        return len(series) - window + idx, val

    def next(self):
        # 1. Environment Confirmation
        is_oversold = self.s9_k[-1] < 20 and self.s14_k[-1] < 20
        is_overbought = self.s9_k[-1] > 80 and self.s14_k[-1] > 80
        
        # 2. Confirmation Candles (Turn up/down)
        bullish_candle = self.data.Close[-1] > self.data.Open[-1]
        bearish_candle = self.data.Close[-1] < self.data.Open[-1]
        
        # 3. Divergence Detection
        long_div = False
        short_div = False
        
        # Bullish Divergence
        p_idx, p_val = self.find_pivot(self.body_low, 'low')
        if p_idx is not None and p_idx < len(self.body_low) - 1:
            prev_p_idx, prev_p_val = self.find_pivot(self.body_low[:-2], 'low', window=15)
            if prev_p_idx is not None:
                if self.body_low[-1] <= prev_p_val and self.s9_k[-1] > self.s9_k[prev_p_idx] and self.s9_k[prev_p_idx] < 25:
                    long_div = True

        # Bearish Divergence
        p_idx, p_val = self.find_pivot(self.body_high, 'high')
        if p_idx is not None and p_idx < len(self.body_high) - 1:
            prev_p_idx, prev_p_val = self.find_pivot(self.body_high[:-2], 'high', window=15)
            if prev_p_idx is not None:
                if self.body_high[-1] >= prev_p_val and self.s9_k[-1] < self.s9_k[prev_p_idx] and self.s9_k[prev_p_idx] > 75:
                    short_div = True

        # 4. Triple Stochastic Flag
        bull_flag = self.s14_k[-1] < 30 and self.s60_k[-1] > 80
        bear_flag = self.s14_k[-1] > 70 and self.s60_k[-1] < 20

        # ENTRY
        if not self.position:
            # Long
            if (is_oversold and long_div and bullish_candle) or (bull_flag and bullish_candle):
                # Ensure we are not trading into a brick wall (200 EMA) if very close
                self.buy(sl=self.data.Low[-1] * 0.997) 
            
            # Short
            elif (is_overbought and short_div and bearish_candle) or (bear_flag and bearish_candle):
                self.sell(sl=self.data.High[-1] * 1.003)

        else:
            # EXIT
            if self.position.is_long:
                # Primary exit: Overbought
                if self.s9_k[-1] > 80 and self.s60_k[-1] < 80:
                    self.position.close()
                # Trailing logic: Close if breaks EMA20 after some profit
                elif self.data.Close[-1] < self.ema20[-1] and self.s9_k[-1] > 60:
                    self.position.close()
            
            elif self.position.is_short:
                if self.s9_k[-1] < 20 and self.s60_k[-1] > 20:
                    self.position.close()
                elif self.data.Close[-1] > self.ema20[-1] and self.s9_k[-1] < 40:
                    self.position.close()

# ========================================
# 4. Execution
# ========================================

if __name__ == "__main__":
    DATA_FILE = sys.argv[1] if len(sys.argv) > 1 else 'gold5min.csv'
    df = load_data(DATA_FILE)
    if df is not None:
        bt = Backtest(df, JohnKuriskoScalp, cash=10000, commission=0.00001, exclusive_orders=True)
        stats = bt.run()
        print(stats)
        bt.plot()
