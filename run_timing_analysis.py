#!/usr/bin/env python3
"""
Simple script to run timing analysis on IVV data
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
import glob
import sys
from typing import Dict, List, Tuple

def analyze_stock_timing(filepath: str, bars_to_check: int = 6) -> Dict:
    """
    Analyze timing patterns for a single stock.
    
    Args:
        filepath (str): Path to CSV file
        bars_to_check (int): Number of initial bars to check (default 6 for 30 minutes)
    
    Returns:
        Dict: Analysis results
    """
    try:
        # Detect CSV format by reading first few lines
        with open(filepath, 'r') as f:
            first_line = f.readline().strip()
            second_line = f.readline().strip()
            third_line = f.readline().strip()
        
        # Check if it's the new format (time,open,high,low,close,Volume)
        if first_line.lower().startswith('time,open,high,low,close,volume'):
            # New format: time,open,high,low,close,Volume
            data = pd.read_csv(filepath)
            data['datetime'] = pd.to_datetime(data['time'], utc=True)
            data = data.set_index('datetime')
            
            # Rename columns to match expected format
            data = data.rename(columns={
                'open': 'Open',
                'high': 'High', 
                'low': 'Low',
                'close': 'Price',  # Use close as Price
                'Volume': 'Volume'
            })
            data = data[['Price', 'High', 'Low', 'Open', 'Volume']]
            
        else:
            # Old format: skip 3 header rows
            data = pd.read_csv(filepath, skiprows=3, header=None)
            
            # The first column is datetime, set it as index and parse dates
            data['datetime'] = pd.to_datetime(data.iloc[:, 0], utc=True)
            data = data.set_index('datetime')
            
            # The remaining columns should be Price, High, Low, Open, Volume
            data.columns = ['Price', 'High', 'Low', 'Open', 'Volume', 'datetime']
            data = data[['Price', 'High', 'Low', 'Open', 'Volume']]  # Keep only the data columns
        
        if data.empty:
            return {"error": f"No data found in {filepath}"}
        
        # Ensure data is sorted by datetime
        data = data.sort_index()
        
        # Group by trading day
        data['date'] = data.index.date
        daily_groups = data.groupby('date')
        
        results = {
            'total_days': 0,
            'high_in_first_n_bars': 0,
            'low_in_first_n_bars': 0,
            'both_high_and_low_in_first_n_bars': 0,
            'file': os.path.basename(filepath)
        }
        
        for date, daily_data in daily_groups:
            # Skip days with insufficient data
            if len(daily_data) < bars_to_check:
                continue
            
            results['total_days'] += 1
            
            # Get first n bars
            first_n_bars = daily_data.head(bars_to_check)
            
            # Get full day data for comparison
            full_day_high = daily_data['High'].max()
            full_day_low = daily_data['Low'].min()
            
            # Check if daily high occurred in first n bars
            first_n_high = first_n_bars['High'].max()
            if abs(first_n_high - full_day_high) < 1e-10:  # Use small epsilon for float comparison
                results['high_in_first_n_bars'] += 1
            
            # Check if daily low occurred in first n bars
            first_n_low = first_n_bars['Low'].min()
            if abs(first_n_low - full_day_low) < 1e-10:  # Use small epsilon for float comparison
                results['low_in_first_n_bars'] += 1
            
            # Check if both high and low occurred in first n bars
            if (abs(first_n_high - full_day_high) < 1e-10 and 
                abs(first_n_low - full_day_low) < 1e-10):
                results['both_high_and_low_in_first_n_bars'] += 1
        
        # Calculate percentages
        if results['total_days'] > 0:
            results['high_percentage'] = (results['high_in_first_n_bars'] / results['total_days']) * 100
            results['low_percentage'] = (results['low_in_first_n_bars'] / results['total_days']) * 100
            results['both_percentage'] = (results['both_high_and_low_in_first_n_bars'] / results['total_days']) * 100
        else:
            results['high_percentage'] = 0
            results['low_percentage'] = 0
            results['both_percentage'] = 0
        
        return results
    
    except Exception as e:
        return {"error": f"Error analyzing {filepath}: {str(e)}"}

def main():
    """Main function to run the timing analysis."""
    print("Stock Timing Analyzer: Analyzes probability that daily high/low occurs in first nbars")
    
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python run_timing_analysis.py <csv_file_path> [num_bars]")
        print("Example: python run_timing_analysis.py data/IVV_5m.csv 6")
        return
    
    filepath = sys.argv[1]
    bars_to_check = 6  # default
    
    if len(sys.argv) >= 3:
        try:
            bars_to_check = int(sys.argv[2])
        except ValueError:
            print("❌ Error: num_bars must be an integer")
            return
    
    # Check if file exists
    if not os.path.exists(filepath):
        print(f"❌ File '{filepath}' not found")
        return
    
    print(f"📁 Analyzing file: {filepath}")
    print(f"📊 Checking first {bars_to_check} bars")
    print("-" * 50)
    
    # Analyze the specified file
    result = analyze_stock_timing(filepath, bars_to_check=bars_to_check)
    
    if "error" in result:
        print(f"❌ {result['error']}")
        return
    
    print(f"📈 Analysis complete:")
    print(f"   Total trading days: {result['total_days']}")
    print(f"   High in first {bars_to_check} bars: {result['high_in_first_n_bars']} ({result['high_percentage']:.1f}%)")
    print(f"   Low in first {bars_to_check} bars: {result['low_in_first_n_bars']} ({result['low_percentage']:.1f}%)")
    print(f"   Both high & low in first {bars_to_check} bars: {result['both_high_and_low_in_first_n_bars']} ({result['both_percentage']:.1f}%)")
    print()
    
    # Additional analysis
    print(f"� Analysis Summary:")
    print(f"   The probability that daily high occurs in first {bars_to_check} bars: {result['high_percentage']:.1f}%")
    print(f"   The probability that daily low occurs in first {bars_to_check} bars: {result['low_percentage']:.1f}%")
    
    # Calculate probability of high OR low in first n bars
    prob_high_or_low = result['high_percentage'] + result['low_percentage'] - result['both_percentage']
    print(f"   The probability that high OR low occurs in first {bars_to_check} bars: {prob_high_or_low:.1f}%")

if __name__ == "__main__":
    main()