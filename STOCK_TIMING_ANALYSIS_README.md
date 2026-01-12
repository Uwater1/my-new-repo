# Stock Timing Analysis Tool

This Python script analyzes whether a stock's daily high or low occurs within the first 30 minutes (6 bars) of trading using 5-minute interval data.

## Overview

The script tests the claim that there's approximately a 50% chance that a stock's daily high or low will occur within the first 30 minutes of trading. This analysis can be useful for traders who want to understand intraday price patterns and timing strategies.

## Features

- Downloads 5-minute interval data using yfinance
- Analyzes daily high/low timing patterns
- Calculates percentages for different scenarios
- Provides clear, formatted output
- Includes comprehensive error handling
- Supports both interactive and programmatic usage

## Files

- `stock_timing_analysis.py`: Main analysis script with interactive CLI
- `example_usage.py`: Demonstrates programmatic usage
- `requirements.txt`: Python dependencies
- `STOCK_TIMING_ANALYSIS_README.md`: This documentation file

## Installation

1. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Required packages:
   - yfinance>=0.2.18
   - pandas>=1.5.0
   - numpy>=1.21.0

## Usage

### Interactive Mode (Command Line)

Run the script and follow the prompts:

```bash
python stock_timing_analysis.py
```

The script will:
1. Prompt for a stock ticker symbol (e.g., IVV, SPY, AAPL)
2. Ask if you want to specify a custom date range
3. Download and analyze the data
4. Display comprehensive results

### Programmatic Usage

Use the `StockTimingAnalyzer` class in your own scripts:

```python
from stock_timing_analysis import StockTimingAnalyzer

# Create analyzer
analyzer = StockTimingAnalyzer('IVV')

# Download and analyze
if analyzer.download_data() and analyzer.preprocess_data():
    results = analyzer.analyze_timing()
    analyzer.display_results()
    
    # Access results programmatically
    print(f"High in first 30 minutes: {results['high_percentage']:.2f}%")
```

### Batch Analysis

Analyze multiple tickers at once:

```python
from stock_timing_analysis import StockTimingAnalyzer

tickers = ['IVV', 'SPY', 'QQQ']

for ticker in tickers:
    analyzer = StockTimingAnalyzer(ticker)
    if analyzer.download_data() and analyzer.preprocess_data():
        results = analyzer.analyze_timing()
        print(f"{ticker}: {results['either_percentage']:.2f}%")
```

## Analysis Details

The script performs the following analysis:

1. **Data Download**: Retrieves 5-minute interval data for the specified ticker
2. **Preprocessing**: Filters data to regular trading hours (9:30 AM - 4:00 PM EST)
3. **Daily Analysis**: For each trading day:
   - Identifies the daily high and low prices
   - Checks if the high occurs within the first 6 bars (30 minutes)
   - Checks if the low occurs within the first 6 bars (30 minutes)
4. **Statistics**: Calculates percentages for:
   - Days with high in first 30 minutes
   - Days with low in first 30 minutes
   - Days with either high or low in first 30 minutes

## Output Interpretation

The script provides clear output with:

- Total number of trading days analyzed
- Count and percentage of days where high occurs in first 30 minutes
- Count and percentage of days where low occurs in first 30 minutes
- Count and percentage of days where either high or low occurs in first 30 minutes
- Interpretation of whether the 50% claim is supported

## Example Output

```
============================================================
STOCK TIMING ANALYSIS RESULTS FOR IVV
============================================================
Analysis Period: 2023-11-11 to 2024-01-11
Total Trading Days Analyzed: 42

DAILY HIGH ANALYSIS:
  Days with high in first 30 minutes: 18
  Percentage: 42.86%

DAILY LOW ANALYSIS:
  Days with low in first 30 minutes: 16
  Percentage: 38.10%

COMBINED ANALYSIS (High OR Low in first 30 minutes):
  Days with either high or low in first 30 minutes: 28
  Percentage: 66.67%

INTERPRETATION:
  📈 ABOVE AVERAGE: High/low occurs in first 30 minutes more often than 50%
  The claim of ~50% probability is NOT SUPPORTED by this analysis.
============================================================
```

## Dependencies

- **yfinance**: For downloading stock data from Yahoo Finance
- **pandas**: For data manipulation and analysis
- **numpy**: For numerical operations
- **datetime**: For date/time handling

## Error Handling

The script includes comprehensive error handling for:

- Invalid ticker symbols
- Network connectivity issues
- Insufficient data
- Data processing errors
- Missing trading data

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome. Please create a pull request with your changes.

## Notes

- The script analyzes regular trading hours only (9:30 AM - 4:00 PM EST)
- Extended hours trading is not included in the analysis
- Results may vary based on the time period analyzed
- The 50% claim is a general observation and may not hold for all stocks or time periods