# John's Project

This repository contains various files and projects related to John's work.

## Contents

- `essay.pdf` - Essay document
- `essay.txt` - Essay text file
- `firstresearch.md` - Research notes
- `gold5min.csv` - Gold price data (5-minute intervals)
- `john.py` - Python script
- `JohnKuriskoScalp.html` - HTML file
- `result.txt` - Result output file
- `video.txt` - Video-related text file

## Strategy Logic (John Kurisko Scalp)

The `john.py` script implements the **DayTraderRockStar (DTRS)** scalping methodology, focusing on high-probability momentum setups using multiple stochastic oscillators.

### Core Indicators
- **Four Stochastics**: Used to define the "Trading Environment" (Quad Rotation).
  - Fast (9,3), Standard (14,3), Medium (44,4), and Slow (60,10,10).
- **Moving Averages**: 20 EMA for momentum/trailing exits and 200 EMA for institutional support/resistance.
- **Body Price Divergence**: Detects momentum shifts using candle body lows/highs rather than wicks.

### Key Setups
1. **Divergence (Long & Short)**: Price makes a lower low while the 9-3 Stochastic makes a higher low (or vice versa for shorts). Combined with a "Quad Rotation" (multiple stochastics oversold/overbought).
2. **Triple Stochastic Flag**: A trend continuation setup where the 14-3 Stochastic pulls back while the 60-10 Stochastic remains "embedded" in a strong trend.
3. **Execution Filters**: trades are confirmed with price action (candle turn) and momentum alignment to increase the win rate.

## License

This project is licensed under the Source Available All Rights Reserved License. See the [LICENSE](LICENSE) file for details.
