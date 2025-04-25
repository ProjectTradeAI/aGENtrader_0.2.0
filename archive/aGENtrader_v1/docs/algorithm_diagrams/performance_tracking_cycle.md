# Performance Tracking Cycle

This document details the performance tracking cycle in the trading system, focusing on how agent decisions are tracked, analyzed, and used to improve agent performance over time.

## Process Overview

The performance tracking cycle is a feedback loop that continuously improves agent performance by analyzing decisions, tracking outcomes, and optimizing agent prompts based on historical data.

## Detailed Algorithm

```
START
|
+----> Decision is made by agents
|      |
|      +----> DecisionSession completes with a decision
|      |
|      +----> Decision contains:
|             - Symbol, Action (BUY/SELL/HOLD)
|             - Confidence level (0-100%)
|             - Current price, Risk level
|             - Reasoning, Timestamp
|
+----> Track decision in database
|      |
|      +----> DecisionTracker.track_session_decision()
|      |      |
|      |      +----> Extract decision details
|      |      |
|      |      +----> Determine market condition
|      |      |
|      |      +----> Identify agent types involved
|      |      |
|      |      +----> Insert record into decisions table
|      |      |
|      |      +----> Return decision_id for future reference
|
+----> Track decision outcome (when available)
|      |
|      +----> DecisionTracker.track_decision_outcome()
|             |
|             +----> Associate outcome with decision_id
|             |
|             +----> Record outcome type (price_change, profit_loss, etc.)
|             |
|             +----> Store outcome value and timestamp
|             |
|             +----> Include any additional context details
|
+----> Analyze agent performance
|      |
|      +----> DecisionTracker.analyze_agent_performance()
|             |
|             +----> Define analysis period (e.g., 30 days)
|             |
|             +----> Query decisions involving the agent
|             |
|             +----> Calculate performance metrics:
|                    - Decision count by type (BUY/SELL/HOLD)
|                    - Average confidence level
|                    - Decision consistency by market condition
|                    - Outcome correlation
|             |
|             +----> Store metrics in performance_metrics table
|
+----> Generate improvement suggestions
|      |
|      +----> DecisionTracker.suggest_prompt_improvements()
|             |
|             +----> Get current agent prompt
|             |
|             +----> Get performance data
|             |
|             +----> Use AgentPromptOptimizer to analyze prompt
|                    |
|                    +----> Analyze prompt patterns:
|                           - Word count, sentence length
|                           - Specificity and clarity scores
|                           - Instruction count
|                           - Vague terms and ambiguities
|                    |
|                    +----> Identify improvement areas based on:
|                           - Decision consistency issues
|                           - Confidence calibration
|                           - Prompt clarity and specificity
|                    |
|                    +----> Generate specific suggestions for each area
|                    |
|                    +----> Create improved prompt version
|
+----> Apply prompt improvements
|      |
|      +----> AgentPromptOptimizer.apply_suggestions()
|             |
|             +----> Back up current agent configuration
|             |
|             +----> Update prompt in configuration file
|             |
|             +----> Log changes for reference
|
+----> Evaluate improved performance (cycle repeats)
|
END
```

## Database Schema

The performance tracking system uses a SQLite database with three main tables:

### 1. decisions

Stores each trading decision made by agents:

| Column           | Type      | Description                               |
|------------------|-----------|-------------------------------------------|
| id               | INTEGER   | Primary key                               |
| session_id       | TEXT      | Unique session identifier                 |
| symbol           | TEXT      | Trading symbol (e.g., BTCUSDT)            |
| timestamp        | TEXT      | ISO timestamp of decision                 |
| current_price    | REAL      | Price at the time of decision             |
| action           | TEXT      | BUY, SELL, or HOLD                        |
| confidence       | REAL      | Confidence level (0-100)                  |
| risk_level       | TEXT      | low, medium, or high                      |
| reasoning        | TEXT      | Explanation for the decision              |
| market_condition | TEXT      | Market condition at time of decision      |
| is_simulated     | INTEGER   | Whether the decision was rule-based (1) or agent-based (0) |
| agent_types      | TEXT      | Comma-separated list of agent types involved |

### 2. outcomes

Tracks the outcomes of decisions:

| Column           | Type      | Description                               |
|------------------|-----------|-------------------------------------------|
| id               | INTEGER   | Primary key                               |
| decision_id      | INTEGER   | Foreign key to decisions table            |
| outcome_type     | TEXT      | Type of outcome (price_change, profit_loss, etc.) |
| outcome_value    | REAL      | Numeric value of the outcome              |
| timestamp        | TEXT      | ISO timestamp of when outcome was recorded |
| details          | TEXT      | Additional JSON details about the outcome  |

### 3. performance_metrics

Stores calculated performance metrics:

| Column           | Type      | Description                               |
|------------------|-----------|-------------------------------------------|
| id               | INTEGER   | Primary key                               |
| agent_type       | TEXT      | Type of agent being analyzed              |
| metric_name      | TEXT      | Name of the metric                        |
| metric_value     | REAL      | Numeric value of the metric               |
| timestamp        | TEXT      | ISO timestamp of calculation              |
| start_date       | TEXT      | Start of the analysis period              |
| end_date         | TEXT      | End of the analysis period                |

## Prompt Analysis and Optimization

The prompt optimization process involves several key steps:

1. **Pattern Analysis**
   - Analyzes word count and sentence structure
   - Identifies vague terms and ambiguities
   - Calculates specificity and clarity scores
   - Counts specific instruction patterns

2. **Performance-Based Improvements**
   - Identifies consistency issues across market conditions
   - Analyzes confidence calibration
   - Evaluates decision distribution
   - Correlates decisions with outcomes

3. **Suggestion Generation**
   - Creates specific improvement suggestions for:
     - Action balance (addressing bias toward specific actions)
     - Confidence calibration (addressing over/under confidence)
     - Prompt clarity (improving readability and structure)
     - Prompt specificity (adding detailed guidance)

4. **Improved Prompt Creation**
   - Integrates suggestions into the existing prompt
   - Maintains the essential instructions and structure
   - Adds specific improvements in prioritized areas
   - Timestamps and tracks changes for reference

## Integration with Decision Session

The performance tracking system integrates with the `DecisionSession` class:

```python
# Create a decision session with tracking enabled
session = DecisionSession(
    symbol="BTCUSDT",
    track_performance=True  # Enable performance tracking
)

# Run the session as normal - tracking happens automatically
result = session.run_session()
```

When `track_performance=True`, the session:
1. Creates a `DecisionTracker` instance
2. Automatically tracks decisions in the database
3. Includes all relevant market data and technical indicators

## Implementation

The main implementation of this algorithm is in:

- `utils/decision_tracker.py`: Contains the `DecisionTracker` class
- `utils/agent_prompt_optimizer.py`: Contains the `AgentPromptOptimizer` class
- `orchestration/decision_session.py`: Integrates tracking into the decision process

Key methods include:

- `DecisionTracker.track_session_decision()`: Records decisions in the database
- `DecisionTracker.track_decision_outcome()`: Records decision outcomes
- `DecisionTracker.analyze_agent_performance()`: Generates performance metrics
- `DecisionTracker.suggest_prompt_improvements()`: Generates improvement suggestions
- `AgentPromptOptimizer.analyze_prompt_patterns()`: Analyzes prompt structures
- `AgentPromptOptimizer.suggest_prompt_improvements()`: Creates improvement suggestions
- `AgentPromptOptimizer.apply_suggestions()`: Updates agent prompts