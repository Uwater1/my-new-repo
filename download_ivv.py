#!/usr/bin/env python3
"""
Simple script to download IVV data for timing analysis
"""

import yfinance as yf
import pandas as pd
import os
from datetime import datetime

def download_ivv_data():
    """Download IVV 5-minute data for the last 60 days"""
    print("Downloading IVV 5-minute data...")
    
    try:
        # Download 60 days of 5-minute data for IVV
        data = yf.download('IVV', period='1y', interval='1m', progress=False)
        
        if data.empty:
            print("❌ No data found for IVV")
            return False
        
        # Filter for regular trading hours (9:30 AM to 4:00 PM EST)
        data = data.sort_index()
        data['time'] = data.index.time
        market_open = pd.Timestamp('09:30').time()
        market_close = pd.Timestamp('16:00').time()
        
        trading_data = data[
            (data['time'] >= market_open) & 
            (data['time'] <= market_close)
        ]
        
        if trading_data.empty:
            print("❌ No trading data found for IVV")
            return False
        
        # Remove the time column before saving
        trading_data = trading_data.drop('time', axis=1)
        
        # Create data directory if it doesn't exist
        if not os.path.exists('data'):
            os.makedirs('data')
        
        # Save to CSV
        filepath = 'data/IVV_5min.csv'
        trading_data.to_csv(filepath)
        
        print(f"✅ Successfully saved {len(trading_data)} data points to {filepath}")
        print(f"   Date range: {trading_data.index.min()} to {trading_data.index.max()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error downloading IVV data: {str(e)}")
        return False

if __name__ == "__main__":
    download_ivv_data()