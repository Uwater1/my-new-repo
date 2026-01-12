# Stock Timing Analysis - Two-Part System

This system consists of two separate scripts that work together to analyze stock timing patterns:

1. **Data Downloader** - Downloads 5-minute interval stock data
2. **Timing Analyzer** - Analyzes the downloaded data to calculate probabilities

## Overview

The system tests the claim that there's approximately a 50% chance that a stock's daily high or low will occur within the first 30 minutes (6 bars) of trading.

## Files

- `data_downloader.py` - Downloads 5-minute interval data for multiple stocks
- `timing_analyzer.py` - Analyzes pre-downloaded CSV data and outputs probabilities
- `requirements.txt` - Python dependencies
- `TWO_PART_SYSTEM_README.md` - This documentation file

## Installation

Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Part 1: Download Data

Run the data downloader to fetch 5-minute interval data:

```bash
python data_downloader.py
```

**Features:**
- Downloads data for multiple stocks simultaneously
- Supports custom date ranges or number of days
- Saves data as CSV files in a `data/` directory
- Includes popular ETFs, stocks, commodities, and forex pairs

**Example output:**
```
🚀 Starting download for 15 stocks...
--------------------------------------------------
📥 Downloading 5-minute data for IVV...
✅ Successfully saved 1260 data points to data/IVV_5min.csv
   Date range: 2023-11-13 09:30:00 to 2024-01-11 16:00:00

📥 Downloading 5-minute data for SPY...
✅ Successfully saved 1260 data points to data/SPY_5min.csv
   Date range: 2023-11-13 09:30:00 to 2024-01-11 16:00:00
...
📊 Download completed!
   Successfully downloaded: 15 stocks
   Failed downloads: 0 stocks
```

### Part 2: Analyze Timing

Run the timing analyzer to calculate probabilities:

```bash
python timing_analyzer.py
```

**Features:**
- Analyzes pre-downloaded CSV files
- Calculates probability for any number of bars (default: 6 bars = 30 minutes)
- Compares multiple stocks side by side
- Provides clear interpretation of results

**Example output:**
```
Stock Timing Analyzer
Analyzes probability that daily high/low occurs in first n bars
======================================================================

📁 Found 15 CSV files:
   1. AAPL
   2. AMZN
   3. BTC-USD
   4. CL=F
   5. EURUSD=X
   6. GC=F
   7. GOOGL
   8. IWM
   9. IVV
  10. MSFT
  11. QQQ
  12. SPY
  13. TSLA
  14. ETH-USD
  15. GBPUSD=X

Or enter specific tickers separated by commas (e.g., IVV,SPY,AAPL)

Enter tickers to analyze (or press Enter for all): IVV,SPY,AAPL
Enter number of bars to analyze (default 6 for 30 minutes): 6

🔍 Analyzing timing patterns for 3 stocks...
📊 Checking first 6 bars (30 minutes)
------------------------------------------------------------

📈 Analyzing IVV...
   ✅ IVV: 66.7% chance

📈 Analyzing SPY...
   ✅ SPY: 61.9% chance

📈 Analyzing AAPL...
   ✅ AAPL: 57.1% chance

================================================================================
STOCK TIMING ANALYSIS RESULTS
First 6 bars (30 minutes)
================================================================================
Ticker   Days   High %   Low %    Either %   Status
--------------------------------------------------------------------------------
IVV      42     42.9     38.1     66.7       📈 ABOVE
SPY      42     40.5     35.7     61.9       📈 ABOVE
AAPL     42     38.1     33.3     57.1       📈 ABOVE
--------------------------------------------------------------------------------
📊 Average probability across all stocks: 61.9%
================================================================================

📋 INTERPRETATION:
   There's approximately a 66.7% chance that today's
   high or low will appear in the first 6 bars (30 minutes) of trading.
   Across all analyzed stocks: 61.9% average probability.
```

## Key Features

### Data Downloader
- **Multiple tickers**: Download data for many stocks at once
- **Flexible date ranges**: Specify custom start/end dates or number of days
- **Automatic filtering**: Only includes regular trading hours (9:30 AM - 4:00 PM EST)
- **Error handling**: Gracefully handles download failures
- **Progress tracking**: Shows download progress for each stock

### Timing Analyzer
- **Offline analysis**: Works with pre-downloaded CSV files
- **Flexible bar count**: Analyze any number of bars (not just 6)
- **Multiple stocks**: Compare timing patterns across different securities
- **Clear output**: Easy-to-read results with interpretation
- **Statistical summary**: Average probabilities across all analyzed stocks

## Output Format

The timing analyzer provides results in this format:
```
There's approximately a m% chance that today's high or low will appear 
on the first n bar (n*5 min)
```

Where:
- `m%` = Probability percentage (e.g., 66.7%)
- `n` = Number of bars (e.g., 6)
- `n*5 min` = Time period in minutes (e.g., 30 minutes)

## Example Results

Based on the analysis, you might get results like:
- "There's approximately a 66.7% chance that today's high or low will appear on the first 6 bar (30 min)"
- "There's approximately a 42.9% chance that today's high or low will appear on the first 4 bar (20 min)"

## Dependencies

- **yfinance**: For downloading stock data (data_downloader.py only)
- **pandas**: For data manipulation and analysis
- **numpy**: For numerical operations
- **colorama**: For enhanced terminal output (optional)

## Benefits of Two-Part System

1. **Offline Analysis**: Once data is downloaded, you can analyze without internet
2. **Data Reusability**: Download data once, analyze multiple times with different parameters
3. **Batch Processing**: Download many stocks at once, then analyze selectively
4. **Flexibility**: Easy to change analysis parameters without re-downloading data
5. **Reliability**: Separates data collection (which can fail due to network issues) from analysis

## Troubleshooting

### Data Downloader Issues
- **Network errors**: Check internet connection and try again
- **Invalid tickers**: Verify ticker symbols are correct
- **Empty data**: Some tickers may not have 5-minute data available

### Timing Analyzer Issues
- **Missing files**: Run data_downloader.py first to create CSV files
- **File format**: Ensure CSV files are in the correct format (5-minute intervals)
- **Insufficient data**: Some days may not have enough trading data in the first n bars

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.