#!/usr/bin/env python3
"""
Stock Timing Analyzer

This script analyzes pre-downloaded 5-minute interval CSV data to determine
the probability that a stock's daily high or low occurs within the first n bars.

Author: Kilo Code
Date: 2026-01-11
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
import glob
from typing import Dict, List, Tuple, Optional


class StockTimingAnalyzer:
    """Analyzes timing patterns in pre-downloaded stock data."""
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize the timing analyzer.
        
        Args:
            data_dir (str): Directory containing CSV files with stock data
        """
        self.data_dir = data_dir
    
    def load_stock_data(self, ticker: str) -> Optional[pd.DataFrame]:
        """
        Load stock data from CSV file.
        
        Args:
            ticker (str): Stock ticker symbol
        
        Returns:
            pd.DataFrame or None: Loaded data or None if file not found
        """
        filename = f"{ticker}_5min.csv"
        filepath = os.path.join(self.data_dir, filename)
        
        if not os.path.exists(filepath):
            print(f"❌ File not found: {filepath}")
            return None
        
        try:
            data = pd.read_csv(filepath, index_col=0, parse_dates=True)
            print(f"✅ Loaded {len(data)} data points for {ticker}")
            return data
        except Exception as e:
            print(f"❌ Error loading {filepath}: {str(e)}")
            return None
    
    def analyze_timing_probability(self, ticker: str, n_bars: int = 6) -> Dict:
        """
        Analyze the probability that daily high/low occurs within first n bars.
        
        Args:
            ticker (str): Stock ticker symbol
            n_bars (int): Number of bars to check (default: 6 for 30 minutes)
        
        Returns:
            Dict: Analysis results with probabilities
        """
        data = self.load_stock_data(ticker)
        
        if data is None:
            return {}
        
        try:
            # Ensure data is sorted by datetime
            data = data.sort_index()
            
            # Add trading day column for grouping
            data['trading_day'] = data.index.date
            
            # Group by trading day
            daily_groups = data.groupby('trading_day')
            
            total_days = 0
            high_in_first_n = 0
            low_in_first_n = 0
            either_in_first_n = 0
            
            for day, day_data in daily_groups:
                total_days += 1
                
                # Sort by time to ensure chronological order
                day_data = day_data.sort_index()
                
                # Get first n bars of trading
                first_n_bars = day_data.head(n_bars)
                
                if len(first_n_bars) < n_bars:
                    # Skip days with insufficient data in first n bars
                    total_days -= 1
                    continue
                
                # Find daily high and low
                daily_high = day_data['High'].max()
                daily_low = day_data['Low'].min()
                
                # Check if high occurs in first n bars
                high_in_first = any(first_n_bars['High'] == daily_high)
                
                # Check if low occurs in first n bars
                low_in_first = any(first_n_bars['Low'] == daily_low)
                
                if high_in_first:
                    high_in_first_n += 1
                
                if low_in_first:
                    low_in_first_n += 1
                
                if high_in_first or low_in_first:
                    either_in_first_n += 1
            
            # Calculate percentages
            if total_days > 0:
                high_percentage = (high_in_first_n / total_days) * 100
                low_percentage = (low_in_first_n / total_days) * 100
                either_percentage = (either_in_first_n / total_days) * 100
            else:
                high_percentage = low_percentage = either_percentage = 0
            
            return {
                'ticker': ticker,
                'total_days_analyzed': total_days,
                'days_with_high_in_first_n': high_in_first_n,
                'days_with_low_in_first_n': low_in_first_n,
                'days_with_either_in_first_n': either_in_first_n,
                'high_percentage': high_percentage,
                'low_percentage': low_percentage,
                'either_percentage': either_percentage,
                'n_bars': n_bars,
                'time_period_minutes': n_bars * 5
            }
            
        except Exception as e:
            print(f"❌ Error analyzing {ticker}: {str(e)}")
            return {}
    
    def analyze_multiple_stocks(self, tickers: List[str], n_bars: int = 6) -> List[Dict]:
        """
        Analyze timing patterns for multiple stocks.
        
        Args:
            tickers (List[str]): List of stock ticker symbols
            n_bars (int): Number of bars to check
        
        Returns:
            List[Dict]: List of analysis results for each stock
        """
        results = []
        
        print(f"🔍 Analyzing timing patterns for {len(tickers)} stocks...")
        print(f"📊 Checking first {n_bars} bars ({n_bars * 5} minutes)")
        print("-" * 60)
        
        for ticker in tickers:
            print(f"\n📈 Analyzing {ticker}...")
            result = self.analyze_timing_probability(ticker, n_bars)
            
            if result:
                results.append(result)
                print(f"   ✅ {ticker}: {result['either_percentage']:.1f}% chance")
            else:
                print(f"   ❌ {ticker}: Analysis failed")
        
        return results
    
    def display_results(self, results: List[Dict], n_bars: int = 6):
        """
        Display analysis results in a clear format.
        
        Args:
            results (List[Dict]): List of analysis results
            n_bars (int): Number of bars analyzed
        """
        if not results:
            print("❌ No results to display")
            return
        
        print("\n" + "="*80)
        print(f"STOCK TIMING ANALYSIS RESULTS")
        print(f"First {n_bars} bars ({n_bars * 5} minutes)")
        print("="*80)
        
        # Sort results by either_percentage descending
        sorted_results = sorted(results, key=lambda x: x['either_percentage'], reverse=True)
        
        print(f"{'Ticker':<8} {'Days':<6} {'High %':<8} {'Low %':<8} {'Either %':<10} {'Status'}")
        print("-" * 80)
        
        for result in sorted_results:
            status = "📈 ABOVE" if result['either_percentage'] > 55 else \
                    "📉 BELOW" if result['either_percentage'] < 45 else "🎯 ~50%"
            
            print(f"{result['ticker']:<8} {result['total_days_analyzed']:<6} "
                  f"{result['high_percentage']:<8.1f} {result['low_percentage']:<8.1f} "
                  f"{result['either_percentage']:<10.1f} {status}")
        
        # Summary statistics
        if len(results) > 1:
            avg_percentage = np.mean([r['either_percentage'] for r in results])
            print("-" * 80)
            print(f"📊 Average probability across all stocks: {avg_percentage:.1f}%")
        
        print("="*80)
    
    def find_csv_files(self) -> List[str]:
        """
        Find all CSV files in the data directory that match the pattern *_5min.csv.
        
        Returns:
            List[str]: List of ticker symbols found
        """
        pattern = os.path.join(self.data_dir, "*_5min.csv")
        csv_files = glob.glob(pattern)
        
        tickers = []
        for filepath in csv_files:
            filename = os.path.basename(filepath)
            ticker = filename.replace("_5min.csv", "")
            tickers.append(ticker)
        
        return sorted(tickers)


def main():
    """Main function to run the timing analyzer."""
    print("Stock Timing Analyzer")
    print("Analyzes probability that daily high/low occurs in first n bars")
    print("=" * 70)
    
    # Initialize analyzer
    analyzer = StockTimingAnalyzer()
    
    # Find available CSV files
    available_tickers = analyzer.find_csv_files()
    
    if not available_tickers:
        print("❌ No CSV files found in data directory")
        print("💡 Run data_downloader.py first to download stock data")
        return
    
    print(f"📁 Found {len(available_tickers)} CSV files:")
    for i, ticker in enumerate(available_tickers, 1):
        print(f"  {i:2d}. {ticker}")
    
    # Get user input
    print(f"\nOr enter specific tickers separated by commas (e.g., IVV,SPY,AAPL)")
    user_input = input("\nEnter tickers to analyze (or press Enter for all): ").strip()
    
    if user_input:
        tickers = [ticker.strip().upper() for ticker in user_input.split(',')]
        # Filter to only include available tickers
        tickers = [t for t in tickers if t in available_tickers]
        if not tickers:
            print("❌ None of the specified tickers were found. Using all available tickers.")
            tickers = available_tickers
    else:
        tickers = available_tickers
    
    # Get number of bars to analyze
    n_bars_input = input(f"Enter number of bars to analyze (default 6 for 30 minutes): ").strip()
    n_bars = 6
    if n_bars_input.isdigit():
        n_bars = int(n_bars_input)
    
    # Analyze and display results
    results = analyzer.analyze_multiple_stocks(tickers, n_bars)
    analyzer.display_results(results, n_bars)
    
    # Show interpretation
    print("\n📋 INTERPRETATION:")
    print(f"   There's approximately a {results[0]['either_percentage']:.1f}% chance that today's")
    print(f"   high or low will appear in the first {n_bars} bars ({n_bars * 5} minutes) of trading.")
    
    if len(results) > 1:
        avg_prob = np.mean([r['either_percentage'] for r in results])
        print(f"   Across all analyzed stocks: {avg_prob:.1f}% average probability.")


if __name__ == "__main__":
    main()