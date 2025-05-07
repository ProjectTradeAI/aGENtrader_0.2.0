"""
aGENtrader v0.2.2 Self-Sanity Checks Implementation

This file contains updated methods for the agent classes to incorporate
self-sanity checks into their output. These methods will be merged into
the appropriate agent classes.
"""

# BaseAnalystAgent analyze method with sanity checks
def updated_analyst_analyze(self, symbol=None, market_data=None, interval=None, **kwargs):
    """
    Analyze market data and generate insights.
    
    This method should be overridden by subclasses.
    
    Args:
        symbol: Trading symbol
        market_data: Pre-fetched market data (optional)
        interval: Time interval
        **kwargs: Additional parameters
        
    Returns:
        Analysis results with passed_sanity_check flag
    """
    # Call the actual implementation (will be overridden by subclasses)
    result = self._analyze_implementation(symbol, market_data, interval, **kwargs)
    
    # Apply sanity checks to the result
    return self.sanitize_output(result)

# BaseDecisionAgent make_decision method with sanity checks
def updated_decision_make_decision(self, symbol, interval, analyses):
    """
    Make a trading decision based on multiple analyses.
    
    Args:
        symbol: Trading symbol
        interval: Time interval
        analyses: List of analysis results from different agents
        
    Returns:
        Decision results
    """
    if not analyses:
        return self.build_error_response(
            "NO_ANALYSES",
            "No analysis results provided for decision making"
        )
        
    # Filter out analyses that failed sanity checks
    valid_analyses = []
    rejected_analyses = []
    
    for analysis in analyses:
        # Check if the analysis passed sanity checks
        if SANITY_CHECKS_AVAILABLE:
            try:
                # Use the utility function to check the passed_sanity_check flag
                if 'passed_sanity_check' in analysis and analysis['passed_sanity_check']:
                    valid_analyses.append(analysis)
                else:
                    # Log warning about rejected analysis
                    agent_name = analysis.get('agent_name', 'Unknown')
                    self.logger.warning(f"Rejected analysis from {agent_name} that failed sanity check")
                    rejected_analyses.append(analysis)
            except Exception as e:
                self.logger.warning(f"Error checking sanity flag: {str(e)}")
                rejected_analyses.append(analysis)
        else:
            # Basic check if utilities aren't available
            if 'error' not in analysis and analysis.get('passed_sanity_check', True):
                valid_analyses.append(analysis)
            else:
                rejected_analyses.append(analysis)
    
    # Log the rejected analyses
    if rejected_analyses:
        agent_names = [a.get('agent_name', 'UnknownAgent') for a in rejected_analyses]
        self.logger.warning(f"Rejected {len(rejected_analyses)} analyses that failed sanity checks: {agent_names}")
    
    # Check if we have any valid analyses left
    if not valid_analyses:
        # Return a safe fallback decision if all analyses failed sanity checks
        return self.build_fallback_decision(
            symbol=symbol,
            interval=interval,
            error_type="All Failed Sanity Check",
            error_message="All analyst agents failed sanity checks"
        )
    
    # Organize the analyses by agent name
    organized_analyses = {}
    for agent_analysis in valid_analyses:
        key = agent_analysis.get('agent_type', 'unknown')
        organized_analyses[key] = agent_analysis
    
    # Implementation-specific decision logic goes here
    # This will be merged with the actual decision-making code
    
    # Apply sanity checks to the final decision
    final_decision = self._decision_implementation(symbol, interval, valid_analyses, organized_analyses)
    return self.sanitize_output(final_decision)

# Fallback decision method for when all analyses fail sanity checks
def build_fallback_decision(self, symbol, interval, error_type, error_message):
    """
    Build a safe fallback decision when normal decision making isn't possible.
    
    Args:
        symbol: Trading symbol
        interval: Time interval
        error_type: Type of error that caused the fallback
        error_message: Detailed error message
        
    Returns:
        Safe fallback decision
    """
    current_time = datetime.now().isoformat()
    
    fallback_decision = {
        "agent_name": self.agent_name,
        "timestamp": current_time,
        "symbol": symbol,
        "interval": interval,
        "signal": "HOLD",  # The safest fallback is always HOLD
        "confidence": 0,
        "directional_confidence": 0,
        "reasoning": f"Fallback decision due to error: {error_message}",
        "error": True,
        "error_type": error_type,
        "error_message": error_message,
        "passed_sanity_check": True  # The fallback itself passes sanity checks
    }
    
    self.logger.warning(f"Using fallback HOLD decision due to {error_type}: {error_message}")
    
    return fallback_decision