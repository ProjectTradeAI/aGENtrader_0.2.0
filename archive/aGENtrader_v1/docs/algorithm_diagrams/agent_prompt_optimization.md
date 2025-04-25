# Agent Prompt Optimization

This document details the agent prompt optimization process, which systematically analyzes and improves agent prompts based on historical performance data.

## Process Overview

The agent prompt optimization process uses historical decision data to identify patterns, strengths, and weaknesses in agent behavior, then generates targeted improvements to agent prompts to enhance decision quality.

## Detailed Algorithm

```
START
|
+----> Initialize AgentPromptOptimizer
|      |
|      +----> Load agent configuration
|      |
|      +----> Connect to decision tracker database
|      |
|      +----> Set analysis parameters
|
+----> Select agent for optimization
|      |
|      +----> Get agent type (MarketAnalyst, RiskManager, etc.)
|      |
|      +----> Load current agent prompt
|      |
|      +----> Identify prompt components:
|             - System instruction
|             - Role definition
|             - Task description
|             - Guidelines/constraints
|             - Output format instructions
|
+----> Analyze historical performance
|      |
|      +----> Query decision database
|      |      |
|      |      +----> Filter by agent type
|      |      |
|      |      +----> Set time period (e.g., last 30 days)
|      |      |
|      |      +----> Include only completed decisions with outcomes
|      |
|      +----> Calculate performance metrics
|             |
|             +----> Decision distribution (BUY/SELL/HOLD percentages)
|             |
|             +----> Decision consistency by market condition
|             |
|             +----> Confidence calibration
|             |
|             +----> Outcome correlation
|             |
|             +----> Response quality metrics
|
+----> Analyze prompt patterns
|      |
|      +----> Text analysis
|      |      |
|      |      +----> Word count and distribution
|      |      |
|      |      +----> Sentence length and complexity
|      |      |
|      |      +----> Imperative vs. descriptive language
|      |      |
|      |      +----> Vague terms and ambiguities
|      |
|      +----> Instruction analysis
|             |
|             +----> Count explicit instructions
|             |
|             +----> Identify instruction types
|             |
|             +----> Measure specificity of each instruction
|             |
|             +----> Check for conflicting instructions
|
+----> Identify improvement areas
|      |
|      +----> Decision bias detection
|      |      |
|      |      +----> Check for bias toward specific actions
|      |      |
|      |      +----> Check for bias in market conditions
|      |
|      +----> Confidence calibration
|      |      |
|      |      +----> Detect overconfidence or underconfidence
|      |      |
|      |      +----> Analyze correlation between confidence and outcomes
|      |
|      +----> Specificity assessment
|      |      |
|      |      +----> Identify vague instructions
|      |      |
|      |      +----> Find areas lacking specific guidelines
|      |
|      +----> Consistency analysis
|             |
|             +----> Identify inconsistent decisions in similar contexts
|             |
|             +----> Find patterns in inconsistent responses
|
+----> Generate improvement suggestions
|      |
|      +----> For each improvement area:
|             |
|             +----> Generate specific textual suggestion
|             |
|             +----> Provide reasoning based on performance data
|             |
|             +----> Suggest prompt changes with before/after examples
|             |
|             +----> Assign priority (high/medium/low)
|
+----> Create improved prompt
|      |
|      +----> Apply high-priority suggestions
|      |
|      +----> Review for coherence and clarity
|      |
|      +----> Format according to agent requirements
|      |
|      +----> Add version tracking metadata
|
+----> Validate improvements
|      |
|      +----> Compare before/after prompts
|      |
|      +----> Estimate impact on decision quality
|      |
|      +----> Create backup of original prompt
|
+----> Apply improved prompt (with approval)
|      |
|      +----> Update agent configuration
|      |
|      +----> Log changes in optimization history
|
END
```

## Prompt Structure Analysis

The system analyzes the structure of agent prompts to identify improvement opportunities:

### 1. Component Identification

Breaks down prompts into key components:

- **Role Definition**: How the agent's role is described
- **Task Description**: What the agent is instructed to do
- **Guidelines/Constraints**: Rules the agent should follow
- **Output Format**: Instructions about how to format responses
- **Examples**: Sample responses provided for reference

### 2. Text Pattern Analysis

Analyzes text patterns within the prompt:

- **Word Count**: Total words and distribution by component
- **Sentence Complexity**: Average sentence length, complexity
- **Language Type**: Ratio of imperative to descriptive language
- **Vague Terms**: Count of ambiguous or imprecise terms
- **Specificity Score**: Overall measure of prompt specificity

### 3. Instruction Quality Analysis

Evaluates the quality of instructions:

- **Instruction Count**: Number of explicit instructions
- **Instruction Types**: Categorizes instructions by purpose
- **Contradiction Score**: Detects potentially conflicting instructions
- **Completeness Score**: Assesses coverage of essential instructions

## Performance-Based Analysis

The system correlates prompt characteristics with performance metrics:

### 1. Decision Distribution

Analyzes distribution of decision types:

- **Action Balance**: Ratio of BUY/SELL/HOLD decisions
- **Expected Distribution**: Based on market conditions
- **Bias Detection**: Identifies consistent bias toward specific actions

### 2. Confidence Calibration

Evaluates how well confidence scores predict outcomes:

- **Average Confidence**: Overall confidence level
- **Confidence by Action**: Confidence patterns by decision type
- **Confidence-Outcome Correlation**: How well confidence predicts success
- **Calibration Score**: Measure of confidence accuracy

### 3. Consistency Analysis

Assesses decision consistency across similar situations:

- **Similar Condition Consistency**: Same decision in similar conditions
- **Temporal Consistency**: Consistency over time
- **Market Condition Response**: Consistent responses to market changes

## Improvement Areas

The system identifies specific areas for prompt improvement:

### 1. Action Balance

Addresses biases toward specific actions:

- **BUY Bias**: Tendency to recommend buying too frequently
- **SELL Reluctance**: Hesitation to recommend selling
- **HOLD Default**: Defaulting to HOLD when uncertain

### 2. Confidence Calibration

Improves accuracy of confidence scores:

- **Overconfidence Correction**: Reducing unjustified high confidence
- **Underconfidence Correction**: Encouraging appropriate confidence
- **Confidence Reasoning**: Requiring explicit reasoning for confidence

### 3. Decision Consistency

Enhances consistency across similar situations:

- **Condition Recognition**: Improving recognition of similar conditions
- **Decision Framework**: Providing clear decision criteria
- **Reference Point Instructions**: Adding specific reference checks

### 4. Prompt Clarity

Improves overall prompt clarity and specificity:

- **Vague Term Replacement**: Replacing ambiguous language
- **Instruction Specificity**: Making instructions more precise
- **Format Clarity**: Clarifying expected output format

## Implementation

The main implementation of this algorithm is in the `AgentPromptOptimizer` class in `utils/agent_prompt_optimizer.py`. Key methods include:

- `analyze_prompt_patterns()`: Analyzes the structure and patterns in the prompt
- `analyze_agent_performance()`: Analyzes historical decision performance
- `identify_improvement_areas()`: Identifies areas needing improvement
- `suggest_prompt_improvements()`: Generates specific improvement suggestions
- `create_improved_prompt()`: Creates a new version of the prompt
- `apply_improved_prompt()`: Updates the agent configuration with the new prompt

## Integration with Decision Tracker

The optimizer integrates with the `DecisionTracker` to access historical performance data:

```python
# Initialize optimizer
optimizer = AgentPromptOptimizer(
    agent_type="MarketAnalyst",
    decision_tracker=tracker
)

# Generate and apply improvements
improvements = optimizer.suggest_prompt_improvements()
improved_prompt = optimizer.create_improved_prompt(improvements)

# Apply the improved prompt (with user approval)
if user_approves:
    optimizer.apply_improved_prompt(improved_prompt)
```

## Metrics Used for Optimization

The system uses several metrics to guide optimization:

1. **Decision Accuracy**: How often decisions align with subsequent market movements
2. **Consistency Score**: Consistency of decisions in similar market conditions
3. **Confidence Calibration**: Correlation between confidence levels and outcomes
4. **Bias Score**: Measure of bias toward specific actions
5. **Response Quality**: Assessment of reasoning clarity and completeness
6. **Prompt Specificity**: Measure of how specific and clear the prompt is
7. **Instruction Clarity**: Assessment of instruction clarity and precision

## Improvement Example

An example of the optimization process:

**Original Prompt Component**:
```
As a Market Analyst, provide your assessment of the market conditions
and recommend actions based on the data.
```

**Performance Issue**:
- Low consistency in decision making
- Tendency to be overconfident in BUY recommendations

**Improvement Suggestion**:
```
As a Market Analyst, systematically analyze market conditions using:
1. Price trends over multiple timeframes (1h, 4h, daily)
2. Volume patterns and anomalies
3. Key technical indicators (RSI, MACD, Bollinger Bands)
4. Support/resistance levels

For each recommendation:
- Explicitly state evidence supporting your view
- Consider both bullish and bearish scenarios
- Rate confidence based on conflicting signals (lower when signals conflict)
- Assign confidence scores as follows:
  * 90%+: Strong consensus across all indicators
  * 70-89%: Majority of indicators align
  * 50-69%: Mixed signals with slight bias
  * <50%: Highly conflicting signals (default to HOLD)
```

**Improvement Rationale**:
- Provides specific analysis steps (reduces inconsistency)
- Requires explicit consideration of opposing views (reduces bias)
- Establishes clear confidence calibration guidelines (improves confidence accuracy)