#!/usr/bin/env python3
"""
Stock Timing Analysis Script

This script analyzes whether a stock's daily high or low occurs within the first 
30 minutes (6 bars) of trading using 5-minute interval data.

The analysis tests the claim that there's approximately a 50% chance that the 
day's high or low will occur within the first 30 minutes of trading.

Author: Kilo Code
Date: 2026-01-11
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, time
import warnings
import sys
from typing import Tuple, Dict, Optional


class StockTimingAnalyzer:
    """Analyzes stock price timing patterns for daily high/low occurrences."""
    
    def __init__(self, ticker: str, start_date: Optional[str] = None, end_date: Optional[str] = None):
        """
        Initialize the analyzer with stock ticker and date range.
        
        Args:
            ticker (str): Stock ticker symbol (e.g., 'IVV', 'SPY', 'AAPL')
            start_date (str, optional): Start date in YYYY-MM-DD format
            end_date (str, optional): End date in YYYY-MM-DD format
        """
        self.ticker = ticker
        self.start_date = start_date
        self.end_date = end_date
        self.data = None
        self.results = {}
        
    def download_data(self) -> bool:
        """
        Download 5-minute interval data for the specified ticker.
        
        Returns:
            bool: True if data download successful, False otherwise
        """
        try:
            print(f"Downloading 5-minute data for {self.ticker}...")
            
            # Suppress yfinance warnings for cleaner output
            warnings.filterwarnings('ignore', category=FutureWarning)
            
            # Download data with 5-minute intervals
            if self.start_date and self.end_date:
                self.data = yf.download(
                    self.ticker,
                    start=self.start_date,
                    end=self.end_date,
                    interval='5m',
                    progress=False
                )
            else:
                # Download last 60 days of data by default
                self.data = yf.download(
                    self.ticker,
                    period='60d',
                    interval='5m',
                    progress=False
                )
            
            if self.data.empty:
                print(f"❌ No data found for {self.ticker}. Please check the ticker symbol.")
                return False
                
            print(f"✅ Successfully downloaded {len(self.data)} data points")
            print(f"📊 Date range: {self.data.index.min()} to {self.data.index.max()}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error downloading data for {self.ticker}: {str(e)}")
            return False
    
    def preprocess_data(self) -> bool:
        """
        Preprocess the downloaded data for analysis.
        
        Returns:
            bool: True if preprocessing successful, False otherwise
        """
        try:
            if self.data is None or self.data.empty:
                print("❌ No data available for preprocessing")
                return False
            
            # Ensure data is sorted by datetime
            self.data = self.data.sort_index()
            
            # Add trading day column for grouping
            self.data['trading_day'] = self.data.index.date
            
            # Filter for regular trading hours (9:30 AM to 4:00 PM EST)
            self.data['time'] = self.data.index.time
            market_open = time(9, 30)
            market_close = time(16, 0)
            
            self.data = self.data[
                (self.data['time'] >= market_open) & 
                (self.data['time'] <= market_close)
            ]
            
            if self.data.empty:
                print("❌ No data found within regular trading hours")
                return False
                
            print(f"📊 Filtered to {len(self.data)} data points within trading hours")
            return True
            
        except Exception as e:
            print(f"❌ Error preprocessing data: {str(e)}")
            return False
    
    def analyze_timing(self) -> Dict:
        """
        Analyze whether daily high/low occurs within first 30 minutes.
        
        Returns:
            Dict: Analysis results including counts and percentages
        """
        try:
            if self.data is None or self.data.empty:
                print("❌ No data available for analysis")
                return {}
            
            # Group by trading day
            daily_groups = self.data.groupby('trading_day')
            
            total_days = 0
            high_in_first_30 = 0
            low_in_first_30 = 0
            either_in_first_30 = 0
            
            for day, day_data in daily_groups:
                total_days += 1
                
                # Sort by time to ensure chronological order
                day_data = day_data.sort_index()
                
                # Get first 6 bars (30 minutes) of trading
                first_6_bars = day_data.head(6)
                
                if len(first_6_bars) < 6:
                    # Skip days with insufficient data in first 30 minutes
                    total_days -= 1
                    continue
                
                # Find daily high and low
                daily_high = day_data['High'].max()
                daily_low = day_data['Low'].min()
                
                # Check if high occurs in first 30 minutes
                high_in_first = any(first_6_bars['High'] == daily_high)
                
                # Check if low occurs in first 30 minutes
                low_in_first = any(first_6_bars['Low'] == daily_low)
                
                if high_in_first:
                    high_in_first_30 += 1
                
                if low_in_first:
                    low_in_first_30 += 1
                
                if high_in_first or low_in_first:
                    either_in_first_30 += 1
            
            # Calculate percentages
            if total_days > 0:
                high_percentage = (high_in_first_30 / total_days) * 100
                low_percentage = (low_in_first_30 / total_days) * 100
                either_percentage = (either_in_first_30 / total_days) * 100
            else:
                high_percentage = low_percentage = either_percentage = 0
            
            self.results = {
                'total_days_analyzed': total_days,
                'days_with_high_in_first_30': high_in_first_30,
                'days_with_low_in_first_30': low_in_first_30,
                'days_with_either_in_first_30': either_in_first_30,
                'high_percentage': high_percentage,
                'low_percentage': low_percentage,
                'either_percentage': either_percentage
            }
            
            return self.results
            
        except Exception as e:
            print(f"❌ Error analyzing timing: {str(e)}")
            return {}
    
    def display_results(self):
        """Display the analysis results in a clear format."""
        if not self.results:
            print("❌ No results to display")
            return
        
        print("\n" + "="*60)
        print(f"STOCK TIMING ANALYSIS RESULTS FOR {self.ticker.upper()}")
        print("="*60)
        print(f"Analysis Period: {self.data.index.min().strftime('%Y-%m-%d')} to {self.data.index.max().strftime('%Y-%m-%d')}")
        print(f"Total Trading Days Analyzed: {self.results['total_days_analyzed']}")
        print()
        
        print("DAILY HIGH ANALYSIS:")
        print(f"  Days with high in first 30 minutes: {self.results['days_with_high_in_first_30']}")
        print(f"  Percentage: {self.results['high_percentage']:.2f}%")
        print()
        
        print("DAILY LOW ANALYSIS:")
        print(f"  Days with low in first 30 minutes: {self.results['days_with_low_in_first_30']}")
        print(f"  Percentage: {self.results['low_percentage']:.2f}%")
        print()
        
        print("COMBINED ANALYSIS (High OR Low in first 30 minutes):")
        print(f"  Days with either high or low in first 30 minutes: {self.results['days_with_either_in_first_30']}")
        print(f"  Percentage: {self.results['either_percentage']:.2f}%")
        print()
        
        # Interpretation
        print("INTERPRETATION:")
        if self.results['either_percentage'] > 55:
            print("  📈 ABOVE AVERAGE: High/low occurs in first 30 minutes more often than 50%")
        elif self.results['either_percentage'] < 45:
            print("  📉 BELOW AVERAGE: High/low occurs in first 30 minutes less often than 50%")
        else:
            print("  🎯 AROUND 50%: High/low occurs in first 30 minutes approximately half the time")
        
        print(f"  The claim of ~50% probability is {'SUPPORTED' if 40 <= self.results['either_percentage'] <= 60 else 'NOT SUPPORTED'} by this analysis.")
        print("="*60)


def main():
    """Main function to run the stock timing analysis."""
    print("Stock Timing Analysis Tool")
    print("Analyzes whether daily high/low occurs within first 30 minutes of trading")
    print()
    
    # Get user input
    ticker = input("Enter stock ticker symbol (e.g., IVV, SPY, AAPL): ").strip().upper()
    
    if not ticker:
        print("❌ Please enter a valid ticker symbol")
        return
    
    # Optional date range
    use_custom_dates = input("Do you want to specify a custom date range? (y/n): ").strip().lower()
    start_date = None
    end_date = None
    
    if use_custom_dates == 'y':
        start_date = input("Enter start date (YYYY-MM-DD): ").strip()
        end_date = input("Enter end date (YYYY-MM-DD): ").strip()
    
    print(f"\nAnalyzing {ticker}...")
    print("-" * 40)
    
    # Create analyzer and run analysis
    analyzer = StockTimingAnalyzer(ticker, start_date, end_date)
    
    if not analyzer.download_data():
        print("❌ Failed to download data. Please check your internet connection and ticker symbol.")
        return
    
    if not analyzer.preprocess_data():
        print("❌ Failed to preprocess data.")
        return
    
    results = analyzer.analyze_timing()
    
    if not results:
        print("❌ Failed to analyze data.")
        return
    
    analyzer.display_results()


if __name__ == "__main__":
    main()