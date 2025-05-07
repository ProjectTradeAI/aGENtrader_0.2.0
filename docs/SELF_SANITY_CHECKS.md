# Self-Sanity Checks for aGENtrader v0.2.2

## Overview

Self-sanity checks are a critical feature in aGENtrader v0.2.2 that ensures the quality and reliability of agent outputs throughout the decision-making pipeline. These checks validate various aspects of agent outputs to prevent incorrect, inconsistent, or malformed data from propagating through the system.

## Implementation

The sanity check system is implemented in the following components:

1. `utils/sanity_check.py`: Contains utility functions for performing various types of sanity checks
2. `agents/base_agent.py`: Integrates sanity checks into the agent lifecycle

## Sanity Check Types

The system performs the following types of checks on agent outputs:

### Required Field Validation

Ensures that all required fields are present in the agent output:
- `agent_name`: Name of the agent generating the output
- `timestamp`: Timestamp when the analysis/decision was made
- `signal`: Trading signal (BUY, SELL, HOLD, NEUTRAL, etc.)
- `confidence`: Confidence score for the signal

### Action Format Validation

Validates that the action format in the agent output is correct:
- Action must be one of: BUY, SELL, HOLD, NEUTRAL, CONFLICTED
- The recommendation object must contain an action field

### Confidence Score Validation

Ensures that confidence scores are valid:
- Confidence must be a numeric value (int or float)
- Confidence must be between 0 and 100
- Confidence must not be NaN or Infinity

### Numeric Field Validation

Validates that numeric fields contain valid numbers:
- Fields like confidence, score, value, probability must be numeric
- They must not be NaN or Infinity

### Data Array Validation

Ensures that data arrays are non-empty and contain valid values:
- Arrays must be non-empty
- Arrays should not contain all zeros (potential data issue)
- Arrays should not contain NaN or Infinity values

## Integration with Agent Pipeline

### BaseAgent

The `BaseAgent` class applies sanity checks to all agent outputs through the `sanitize_output` method, which:
1. Adds missing metadata (agent_name, timestamp)
2. Runs all sanity checks on the output
3. Sets the `passed_sanity_check` flag based on the check results

### DecisionAgent

The `BaseDecisionAgent` class filters analysis inputs to include only those that passed sanity checks:
1. Filters out analyses that failed their own sanity checks
2. Issues a warning if all analyses failed sanity checks
3. Applies sanity checks to its own output

## Handling Failed Checks

When an analysis fails sanity checks:
1. The agent sets `passed_sanity_check: false` in its output
2. The failed analysis is excluded from decision making
3. Warning logs are generated with details about the failure

Error response objects from agents automatically have `passed_sanity_check: false`.

## Fallback Behavior

If the sanity check utilities are not available (import fails), the system falls back to basic validation in the `BaseAgent` class, which includes:
1. Checking that output is not empty
2. Basic validation of recommendation and confidence
3. Setting the `passed_sanity_check` flag accordingly

## Example

```python
# Example of an output that passes all sanity checks
valid_output = {
    "agent_name": "TechnicalAnalystAgent",
    "timestamp": "2025-05-06T12:34:56.789Z",
    "signal": "BUY",
    "confidence": 85,
    "reasoning": "Moving averages and RSI indicate a bullish trend",
    "recommendation": {
        "action": "BUY",
        "confidence": 85
    }
}

# Example of an output that fails sanity checks
invalid_output = {
    "agent_name": "SentimentAnalystAgent",
    "timestamp": "2025-05-06T12:34:56.789Z",
    # Missing signal
    "confidence": "invalid",  # Not a number
    "reasoning": "Sentiment analysis shows mixed signals"
}
```

## Testing

The sanity check system is tested in:
1. `tests/test_sanity_checks.py`: Unit tests for individual sanity check functions
2. `tests/test_decision_agent_sanity.py`: Integration tests for sanity checks in the decision pipeline

## Best Practices

1. Always check the `passed_sanity_check` flag before using agent outputs
2. Log and report sanity check failures for debugging
3. Add custom sanity checks in agent subclasses as needed for domain-specific validation
4. Update required fields and validation rules as the system evolves