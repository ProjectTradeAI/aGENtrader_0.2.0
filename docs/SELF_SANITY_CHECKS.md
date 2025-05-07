# Self-Sanity Checks

## Overview

Self-sanity checks provide a critical validation layer within the aGENtrader system to ensure data consistency and prevent invalid outputs from propagating through the decision-making pipeline. These checks help maintain system reliability by detecting and filtering problematic inputs before they impact trading decisions.

## Implementation Details

### Validation Levels

The system implements several validation levels:

1. **Required Field Validation**: Ensures all essential fields are present in agent outputs.
2. **Action Format Validation**: Verifies that signals/actions conform to the expected vocabulary.
3. **Confidence Score Validation**: Ensures confidence scores are within valid ranges (0-100).
4. **Numeric Field Validation**: Checks that numeric values are non-NaN and within reasonable ranges.

### Integration Points

Self-sanity checks are integrated at key points in the agent workflow:

- **BaseAgent.sanitize_output()**: Called automatically before any agent returns results, providing a first layer of validation.
- **DecisionAgent.make_decision()**: Filters out analyses that fail sanity checks to prevent them from influencing the final decision.

## Testing Sanity Checks

The testing harness provides comprehensive tools for testing and evaluating the sanity check functionality:

### Command Line Options

```bash
python3 tests/test_harness.py --sanity-check-test --full-cycle --symbol BTC/USDT --interval 1h
```

Key parameters:
- `--sanity-check-test`: Enables sanity check testing mode
- `--full-cycle`: Runs full decision cycle with all agents
- `--trade-cycle`: Runs full trade cycle (analysis, decision, and trade planning)

### How Sanity Check Testing Works

When sanity check testing is enabled:

1. The test harness injects invalid data (with missing fields, invalid signals, etc.) into the analysis results
2. The DecisionAgent should filter out these invalid analyses
3. The test output shows which analyses passed or failed sanity checks
4. The summary report includes a "Sanity Check" status for each analysis

### Example Test Output

```
## Technical Analysis
  Signal:      BUY
  Confidence:  65%
  Sanity Check: ✓ Passed

## Invalid Analysis
  Signal:      INVALID_SIGNAL
  Confidence:  150%
  Sanity Check: ✗ Failed: Invalid signal type: INVALID_SIGNAL
```

## Implementation Benefits

1. **Robust Decision Making**: Prevents invalid or corrupted data from influencing trading decisions.
2. **Early Error Detection**: Identifies problematic analyses before they can affect downstream components.
3. **Debugging Support**: Provides clear feedback on why analyses were rejected.
4. **System Integrity**: Ensures all components operate with reliable, validated data.

## Configuration

Sanity check thresholds and rules can be adjusted in `utils/sanity_check.py`.

Key configuration options:
- `VALID_SIGNALS`: Set of allowed signal values
- `MIN_CONFIDENCE`: Minimum allowed confidence score (default: 0)
- `MAX_CONFIDENCE`: Maximum allowed confidence score (default: 100)
- `REQUIRED_FIELDS`: Essential fields that must be present in analysis output

## Error Handling

When an analysis fails sanity checks:
1. The problematic analysis is marked with `passed_sanity_check = False`
2. An error message is attached via `sanity_check_error` field
3. The DecisionAgent filters out the analysis from consideration
4. The error is logged for debugging purposes

## Future Enhancements

Planned enhancements to the sanity check system:
1. **Confidence-Based Filtering**: Adjustable thresholds based on market conditions
2. **Historical Validation**: Compare outputs against historical patterns
3. **Cross-Agent Validation**: Cross-check analyses for consistency across agents