# Agent Performance Tracking and Prompt Optimization

This module provides utilities for tracking agent performance and optimizing prompts based on historical decision data.

## Overview

The performance tracking system records and analyzes agent decision-making patterns over time, helping to:

1. Identify inconsistencies in agent decisions
2. Track confidence calibration
3. Analyze decision patterns across different market conditions
4. Generate specific suggestions for improving agent prompts

## Components

### 1. Decision Tracker

The `DecisionTracker` class is responsible for:
- Recording agent decisions in a SQLite database
- Tracking decision outcomes
- Analyzing decision patterns over time
- Generating performance metrics

The tracker integrates directly with the `DecisionSession` class, automatically recording each trading decision when `track_performance=True` is enabled.

### 2. Agent Prompt Optimizer

The `AgentPromptOptimizer` class provides:
- Analysis of prompt patterns (specificity, clarity, ambiguity)
- Generation of prompt improvement suggestions
- Application of improvements to agent configurations
- Automatic backup of previous prompt versions

### 3. Integration with Decision Sessions

The decision tracking system integrates seamlessly with existing decision sessions:

```python
# Create a decision session with tracking enabled
session = DecisionSession(
    symbol="BTCUSDT",
    track_performance=True  # Enable performance tracking
)

# Run the session as normal
result = session.run_session()
```

The session will automatically track each decision in the database, including:
- The trading action (BUY/SELL/HOLD)
- Confidence level
- Risk assessment
- Market conditions
- Technical indicators

## Usage

### Analyzing Agent Performance

To analyze agent performance and generate a comprehensive report:

```bash
python analyze_agent_performance.py --days 30 --agents MarketAnalyst RiskManager
```

### Optimizing Agent Prompts

To generate and apply prompt improvements for a specific agent:

```bash
python optimize_agent_prompts.py --agent MarketAnalyst --days 30
```

This interactive tool will:
1. Analyze the agent's historical performance
2. Identify areas for improvement
3. Generate specific prompt suggestions
4. Create an improved prompt version
5. Allow you to apply the improvements

Use the `--auto-apply` flag to automatically apply suggested improvements without prompting.

### Testing the System

To verify the performance tracking system is working correctly:

```bash
python test_agent_performance_tracking.py
```

## Schema

### Decision Database Schema

The system uses a SQLite database with the following tables:

1. **decisions**: Records each trading decision
   - ID, session_id, symbol, timestamp
   - action, confidence, risk_level, reasoning
   - market_condition, is_simulated, agent_types

2. **outcomes**: Tracks outcomes of previous decisions
   - ID, decision_id, outcome_type, outcome_value
   - timestamp, details (JSON)

3. **performance_metrics**: Stores calculated performance metrics
   - ID, agent_type, metric_name, metric_value
   - timestamp, start_date, end_date

## Development Guidelines

When extending the performance tracking system:

1. Use the `DecisionTracker` instance provided by the `DecisionSession` instead of creating a new one
2. Add decision outcomes using `track_decision_outcome()` once results are known
3. Store new agent prompts in the standard config file for consistency
4. Use the optimizer's backup functionality to keep version history