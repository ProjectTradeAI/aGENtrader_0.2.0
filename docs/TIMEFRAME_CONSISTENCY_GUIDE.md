# Timeframe Consistency Checker

This document provides an overview of the timeframe consistency checker implemented for the aGENtrader v2 system.

## Overview

The timeframe consistency checker is a utility for validating that OHLCV (Open, High, Low, Close, Volume) market data returned from Binance API is consistent across different timeframes. It ensures that data from different intervals (1h, 4h, 1d) is properly aligned and contains realistic price ranges.

## Purpose

The main goals of this tool are to:

1. Verify data consistency between timeframes
2. Ensure timestamps align within expected ranges
3. Validate that price ranges across timeframes are realistic and synchronized
4. Provide detailed logs for review and debugging

## How It Works

The consistency checker:

1. Fetches OHLCV data from Binance for specified timeframes
2. Aligns the data to a common end time (now)
3. Compares timestamps and price ranges across timeframes
4. Generates detailed logs and a summary report
5. Identifies potential inconsistencies for investigation

## Usage

### Basic Usage

```bash
./run_timeframe_consistency_check.sh
```

This will run the consistency check with default settings:
- Symbol: BTC/USDT
- Intervals: 1h, 4h, 1d
- Number of candles: 20

### Advanced Usage

```bash
python scripts/check_timeframe_consistency.py --symbol ETH/USDT --intervals 1h 4h 1d --candles 30
```

Available parameters:
- `--symbol`: Trading symbol to check (default: BTC/USDT)
- `--intervals`: Time intervals to check (default: 1h 4h 1d)
- `--candles`: Number of candles to fetch per interval (default: 20)
- `--output`: Output file path (default: logs/timeframe_data_debug.jsonl)
- `--binance-api-key`: Binance API key (optional for public endpoints)
- `--binance-api-secret`: Binance API secret (optional for public endpoints)

## Output

The consistency checker produces:

1. **Console output**: Shows a summary table of the results and any identified issues
2. **JSONL log file**: Contains detailed data for each timeframe in JSON format
3. **Warning messages**: Displays specific inconsistencies that require attention

## Consistency Checks

The tool performs several key consistency checks:

### 1. Data Completeness
Verifies that the requested number of candles was successfully retrieved for each timeframe.

### 2. Timestamp Alignment
Ensures that the end times across timeframes are reasonably aligned (within 4 hours difference).

### 3. Price Range Consistency
Validates that price ranges (minimum and maximum prices) are consistent across timeframes. A price difference greater than 5% between timeframes triggers a warning.

## Example Output

```
Timeframe Consistency Check Results:
+----------+---------+-------------------+-------------------+-----------+-----------+-------+
| Interval | Candles | Start             | End               | Price Min | Price Max | Error |
+----------+---------+-------------------+-------------------+-----------+-----------+-------+
| 1h       | 20      | 2025-04-22T08:00  | 2025-04-23T04:00  | $84,361   | $84,754   |       |
| 4h       | 20      | 2025-04-15T08:00  | 2025-04-23T04:00  | $84,288   | $85,321   |       |
| 1d       | 20      | 2025-04-03T00:00  | 2025-04-23T00:00  | $63,217   | $85,321   |       |
+----------+---------+-------------------+-------------------+-----------+-----------+-------+

⚠️ Warning: Price ranges differ by more than 5% between timeframes
  Min price difference: 25.38%
  Max price difference: 0.67%

⚠️ Consistency check completed with warnings. See above for details.
```

## Troubleshooting

If you encounter warnings:

1. **Missing data**: Verify connectivity to Binance API and check API key restrictions
2. **Timestamp misalignment**: This may occur during market outages or API issues
3. **Price inconsistencies**: Significant price differences between timeframes might indicate data quality issues or market anomalies

## Integration with Testing

The consistency checker can be integrated into nightly testing:

```bash
# Run as part of nightly tests
./run_timeframe_consistency_check.sh >> nightly_test_log.txt
```

## Dependencies

The script uses:
- Python's standard libraries
- Optional: pandas (for data analysis)
- Optional: tabulate (for table formatting)

If the optional dependencies are not available, the script will use simplified fallback implementations.

## Future Enhancements

Potential future improvements:
- Add support for more extensive validation rules
- Include volume consistency checks
- Implement automated alerting for persistent inconsistencies
- Enable comparison between different data providers