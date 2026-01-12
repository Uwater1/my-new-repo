#!/usr/bin/env python3
"""
Example usage of the Stock Timing Analysis script.

This demonstrates how to use the StockTimingAnalyzer class programmatically
instead of through the interactive command-line interface.
"""

from stock_timing_analysis import StockTimingAnalyzer


def example_analysis():
    """Example of how to use the StockTimingAnalyzer class."""
    
    print("Stock Timing Analysis - Programmatic Example")
    print("=" * 50)
    
    # Create analyzer for IVV (iShares Core S&P 500 ETF)
    analyzer = StockTimingAnalyzer('IVV')
    
    # Download data
    if not analyzer.download_data():
        print("Failed to download data")
        return
    
    # Preprocess data
    if not analyzer.preprocess_data():
        print("Failed to preprocess data")
        return
    
    # Analyze timing patterns
    results = analyzer.analyze_timing()
    
    if not results:
        print("Failed to analyze data")
        return
    
    # Display results
    analyzer.display_results()
    
    # You can also access individual results programmatically
    print("\nProgrammatic Access to Results:")
    print(f"Total days analyzed: {results['total_days_analyzed']}")
    print(f"High in first 30 minutes: {results['high_percentage']:.2f}%")
    print(f"Low in first 30 minutes: {results['low_percentage']:.2f}%")
    print(f"Either high or low in first 30 minutes: {results['either_percentage']:.2f}%")


def batch_analysis():
    """Example of analyzing multiple tickers."""
    
    print("\nBatch Analysis Example")
    print("=" * 30)
    
    tickers = ['IVV', 'SPY', 'QQQ']
    
    for ticker in tickers:
        print(f"\nAnalyzing {ticker}...")
        analyzer = StockTimingAnalyzer(ticker)
        
        if analyzer.download_data() and analyzer.preprocess_data():
            results = analyzer.analyze_timing()
            if results:
                print(f"  {ticker}: {results['either_percentage']:.2f}% of days have high/low in first 30 minutes")


if __name__ == "__main__":
    # Run single example
    example_analysis()
    
    # Run batch example
    batch_analysis()