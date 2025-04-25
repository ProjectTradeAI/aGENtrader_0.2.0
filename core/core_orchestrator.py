"""
Core Orchestrator Module

This module coordinates the multi-agent trading system:
- Initializes and manages all agents
- Triggers analysis workflows
- Collects and integrates agent outputs
- Handles the decision-making process
"""

import os
import sys
import json
import time
import logging
import traceback
from typing import Dict, List, Any, Optional, Union, Tuple

# Add parent directory to path to allow importing from other modules
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

# Import agent modules
from agents.liquidity_analyst_agent import LiquidityAnalystAgent
from agents.technical_analyst_agent import TechnicalAnalystAgent
from agents.sentiment_analyst_agent import SentimentAnalystAgent
from agents.decision_agent import DecisionAgent
from agents.portfolio_manager_agent import PortfolioManagerAgent, TradeValidationStatus
from agents.risk_guard_agent import RiskGuardAgent, RiskApprovalStatus
from agents.position_sizer_agent import PositionSizerAgent
from agents.trade_executor_agent import TradeExecutorAgent

# Import utility modules
from utils.config import get_config
from utils.logger import get_logger

# Import error handling utilities
from utils.error_handler import (
    DataFetchingError,
    ValidationError,
    TradeExecutionError,
    MockDataFallbackError,
    RetryExhaustedError,
    handle_trade_execution_error
)

# Get module logger and configuration
logger = get_logger("orchestrator")
config = get_config()

class CoreOrchestrator:
    """
    Core Orchestrator that coordinates the multi-agent trading system.
    
    This class:
    - Initializes and manages all agents
    - Triggers analysis workflows
    - Collects and integrates agent outputs
    - Handles the decision-making process
    """
    
    def __init__(self):
        """Initialize the Core Orchestrator."""
        self.logger = get_logger("orchestrator")
        
        # Get configuration from central config module
        self.agent_config = config.get_section("agents")
        self.trading_config = config.get_section("trading")
        
        # Load agent weights
        self.agent_weights = config.get_section("agent_weights")
        if not self.agent_weights:
            self.agent_weights = {
                "LiquidityAnalystAgent": 1.0,
                "TechnicalAnalystAgent": 1.2
            }
            self.logger.warning("Agent weights not found in config, using defaults")
        
        # Set default parameters
        self.default_symbol = self.trading_config.get("default_pair", "BTC/USDT")
        self.default_interval = self.trading_config.get("default_interval", "1h")
        self.fallback_decision_enabled = self.trading_config.get("fallback_decision_enabled", True)
        
        # Initialize agent registry
        self.agents = {}
        
        # Initialize agents based on config
        self._init_agents()
        
        self.logger.info(f"Core Orchestrator initialized with agents: {', '.join(self.agents.keys())}")
    
    def _init_agents(self) -> None:
        """Initialize agents based on configuration."""
        # Get list of active agents from configuration
        active_agents = self.agent_config.get("active_agents", [])
        
        # Initialize liquidity analyst if enabled
        if "LiquidityAnalyst" in active_agents and config.is_agent_active("liquidity_analyst"):
            self.agents["liquidity_analyst"] = LiquidityAnalystAgent()
            self.logger.info("Liquidity Analyst Agent initialized")
        
        # Initialize technical analyst if enabled
        if "TechnicalAnalyst" in active_agents and config.is_agent_active("technical_analyst"):
            self.agents["technical_analyst"] = TechnicalAnalystAgent()
            self.logger.info("Technical Analyst Agent initialized")
            
        # Initialize sentiment analyst if enabled
        if "SentimentAnalyst" in active_agents and config.is_agent_active("sentiment_analyst"):
            self.agents["sentiment_analyst"] = SentimentAnalystAgent()
            self.logger.info("Sentiment Analyst Agent initialized")
        
        # Initialize decision agent (always enabled)
        self.agents["decision"] = DecisionAgent()
        self.logger.info("Decision Agent initialized")
        
        # Trade execution pipeline agents
        
        # Initialize Portfolio Manager Agent
        if "PortfolioManager" in active_agents and config.is_agent_active("portfolio_manager"):
            self.agents["portfolio_manager"] = PortfolioManagerAgent()
            self.logger.info("Portfolio Manager Agent initialized")
        else:
            self.agents["portfolio_manager"] = PortfolioManagerAgent()  # Always initialize for trade execution
            self.logger.info("Portfolio Manager Agent initialized (default)")

        # Initialize Risk Guard Agent
        if "RiskGuard" in active_agents and config.is_agent_active("risk_guard"):
            self.agents["risk_guard"] = RiskGuardAgent()
            self.logger.info("Risk Guard Agent initialized")
        else:
            self.agents["risk_guard"] = RiskGuardAgent()  # Always initialize for trade execution
            self.logger.info("Risk Guard Agent initialized (default)")
            
        # Initialize Position Sizer Agent
        if "PositionSizer" in active_agents and config.is_agent_active("position_sizer"):
            self.agents["position_sizer"] = PositionSizerAgent()
            self.logger.info("Position Sizer Agent initialized")
        else:
            self.agents["position_sizer"] = PositionSizerAgent()  # Always initialize for trade execution
            self.logger.info("Position Sizer Agent initialized (default)")
            
        # Initialize Trade Executor Agent
        if "TradeExecutor" in active_agents and config.is_agent_active("trade_executor"):
            self.agents["trade_executor"] = TradeExecutorAgent()
            self.logger.info("Trade Executor Agent initialized")
        else:
            self.agents["trade_executor"] = TradeExecutorAgent()  # Always initialize for trade execution
            self.logger.info("Trade Executor Agent initialized (default)")
            
        # Future: Initialize other agents as they are implemented
        # if "MarketAnalyst" in active_agents and config.is_agent_active("market_analyst"):
        #     from agents.market_analyst_agent import MarketAnalystAgent
        #     self.agents["market_analyst"] = MarketAnalystAgent()
    
    def process_market_event(self, market_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a market event from the live data feed.
        
        Args:
            market_event: Market event data dictionary from MarketDataFetcher
            
        Returns:
            Trading decision dictionary
        """
        self.logger.info(f"Processing market event for {market_event.get('symbol', 'unknown')}")
        
        # Extract symbol and interval from market event
        symbol = market_event.get("symbol", self.default_symbol)
        
        # For now, we use the default interval since market events don't specify it
        interval = self.default_interval
        
        # Initialize results dictionary
        results = {
            "symbol": symbol,
            "interval": interval,
            "timestamp": market_event.get("timestamp", time.strftime("%Y-%m-%d %H:%M:%S")),
            "analyses": {},
            "market_data": market_event,
            "decision": None
        }
        
        # Run analysis workflow with the market event data
        return self._run_analysis_workflow(results, market_event)
    
    def run_analysis(self, 
                   symbol: Optional[str] = None, 
                   interval: Optional[str] = None) -> Dict[str, Any]:
        """
        Run a complete analysis workflow.
        
        Args:
            symbol: Trading symbol (default from config)
            interval: Time interval (default from config)
            
        Returns:
            Dictionary with analysis results and trading decision
        """
        symbol = symbol or self.default_symbol
        interval = interval or self.default_interval
        
        self.logger.info(f"Starting analysis workflow for {symbol} at {interval} interval")
        
        # Initialize results dictionary
        results = {
            "symbol": symbol,
            "interval": interval,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "analyses": {},
            "decision": None
        }
        
        # Run the core analysis workflow (without market event data)
        return self._run_analysis_workflow(results)
    
    def _run_analysis_workflow(self, 
                             results: Dict[str, Any], 
                             market_event: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Internal method to run the core analysis workflow.
        
        Args:
            results: Partial results dictionary
            market_event: Optional market event data
            
        Returns:
            Completed results dictionary with analysis and decision
        """
        start_time = time.time()
        
        try:
            # Validate input parameters
            if not isinstance(results, dict):
                raise ValidationError(f"Results parameter must be a dictionary, got {type(results)}")
                
            symbol = results.get("symbol", self.default_symbol)
            interval = results.get("interval", self.default_interval)
            
            # Ensure analyses dictionary exists
            if "analyses" not in results:
                results["analyses"] = {}
                
            self.logger.info(f"Starting analysis workflow for {symbol} at {interval} interval")
            
            # Step 1: Run all enabled analyst agents
            for agent_name, agent in self.agents.items():
                # Skip decision agent for now
                if agent_name == "decision":
                    continue
                
                # Skip execution pipeline agents
                if agent_name in ["portfolio_manager", "risk_guard", "position_sizer", "trade_executor"]:
                    continue
                
                self.logger.info(f"Running {agent_name} analysis")
                try:
                    # Run analysis
                    if agent_name == "liquidity_analyst":
                        # Ensure symbol format is correct for this agent (no slash)
                        formatted_symbol = symbol.replace("/", "") if "/" in symbol else symbol
                        
                        # If we have market event data with orderbook, pass it to the agent
                        if market_event and "orderbook" in market_event:
                            results["analyses"]["liquidity_analysis"] = agent.analyze(
                                formatted_symbol, 
                                interval,
                                market_data=market_event
                            )
                        else:
                            results["analyses"]["liquidity_analysis"] = agent.analyze(formatted_symbol, interval)
                            
                    elif agent_name == "technical_analyst":
                        # Ensure symbol format is correct for this agent (no slash)
                        formatted_symbol = symbol.replace("/", "") if "/" in symbol else symbol
                        
                        # If we have market event data with OHLCV, pass it to the agent
                        if market_event and "ohlcv" in market_event:
                            results["analyses"]["technical_analysis"] = agent.analyze(
                                formatted_symbol, 
                                interval,
                                market_data=market_event
                            )
                        else:
                            results["analyses"]["technical_analysis"] = agent.analyze(formatted_symbol, interval)
                            
                    elif agent_name == "sentiment_analyst":
                        # Ensure symbol format is correct for this agent (no slash)
                        formatted_symbol = symbol.replace("/", "") if "/" in symbol else symbol
                        
                        # Run sentiment analysis
                        results["analyses"]["sentiment_analysis"] = agent.analyze(formatted_symbol, interval)
                    
                    # Add other agent types here as they are implemented
                except DataFetchingError as e:
                    # Handle data fetching errors
                    error_msg = f"Data fetching error in {agent_name} analysis: {str(e)}"
                    self.logger.error(error_msg)
                    self.logger.error(f"Stack trace: {traceback.format_exc()}")
                    
                    # Store error in results
                    results["analyses"][f"{agent_name}_error"] = {
                        "error": True,
                        "type": "data_fetching",
                        "message": str(e),
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                except RetryExhaustedError as e:
                    # Handle retry exhausted errors
                    error_msg = f"Retry attempts exhausted in {agent_name} analysis: {str(e)}"
                    self.logger.error(error_msg)
                    self.logger.error(f"Stack trace: {traceback.format_exc()}")
                    
                    # Store error in results
                    results["analyses"][f"{agent_name}_error"] = {
                        "error": True,
                        "type": "retry_exhausted",
                        "message": str(e),
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                except MockDataFallbackError as e:
                    # Handle mock fallback not allowed errors
                    error_msg = f"Mock data fallback not allowed in {agent_name} analysis: {str(e)}"
                    self.logger.error(error_msg)
                    
                    # Store error in results
                    results["analyses"][f"{agent_name}_error"] = {
                        "error": True,
                        "type": "mock_fallback_not_allowed",
                        "message": str(e),
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                except Exception as e:
                    # Handle unexpected errors
                    error_msg = f"Unexpected error in {agent_name} analysis: {str(e)}"
                    self.logger.error(error_msg)
                    self.logger.error(f"Stack trace: {traceback.format_exc()}")
                    
                    # Store error in results
                    results["analyses"][f"{agent_name}_error"] = {
                        "error": True,
                        "type": "unexpected",
                        "message": str(e),
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
            
            # Step 2: Make trading decision
            if "decision" in self.agents:
                self.logger.info("Making trading decision")
                try:
                    # Validate analyses results
                    valid_analyses = {}
                    error_analyses = {}
                    
                    for key, value in results["analyses"].items():
                        if isinstance(value, dict) and value.get("error", False):
                            error_analyses[key] = value
                        else:
                            valid_analyses[key] = value
                    
                    # Log any errors encountered
                    if error_analyses:
                        self.logger.warning(f"Some analyses have errors: {list(error_analyses.keys())}")
                    
                    # Check if we have any valid analyses
                    if not valid_analyses:
                        raise ValidationError("No valid analyses available for decision making")
                    
                    # Pass agent weights to the decision agent
                    results["decision"] = self.agents["decision"].make_decision(
                        valid_analyses,
                        symbol,
                        interval,
                        agent_weights_override=self.agent_weights
                    )
                    
                    # Log decision
                    self.agents["decision"].log_decision(results["decision"])
                except Exception as e:
                    self.logger.error(f"Error making trading decision: {str(e)}")
                    self.logger.error(f"Stack trace: {traceback.format_exc()}")
                    
                    # Use fallback decision if enabled in config
                    if self.fallback_decision_enabled:
                        self.logger.info("Using fallback decision due to error")
                        # Create a fallback decision with agent contributions
                        agent_contributions = {}
                        for agent_name in self.agent_weights:
                            agent_weight = self.agent_weights.get(agent_name, 1.0)
                            agent_contributions[agent_name] = {
                                "action": "HOLD",
                                "confidence": 0,
                                "weight": agent_weight,
                                "weighted_confidence": 0
                            }
                        
                        results["decision"] = {
                            "action": "HOLD",
                            "pair": symbol,
                            "confidence": 0,
                            "reason": f"Error in decision process: {str(e)}",
                            "agent_contributions": agent_contributions,
                            "decision_method": "error_fallback",
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "error": str(e)
                        }
                    else:
                        self.logger.warning("Fallback decision is disabled in config")
                        results["decision"] = {
                            "error": True,
                            "message": f"Decision making failed: {str(e)}",
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                        }
            
            # Log completion and timing
            elapsed_time = time.time() - start_time
            self.logger.info(f"Analysis workflow completed in {elapsed_time:.2f} seconds")
            
            # Step 3: Execute trade pipeline if we have a valid decision
            if (results.get("decision") and 
                isinstance(results["decision"], dict) and 
                not results["decision"].get("error", False) and 
                results["decision"].get("action") != "HOLD"):
                
                decision_action = results["decision"].get("action", "UNKNOWN")
                self.logger.info(f"Processing trade execution pipeline for {decision_action} decision")
                
                try:
                    # Make a safe copy of the decision as a dictionary
                    decision_dict = dict(results["decision"])
                    
                    # Execute trade pipeline
                    trade_result = self._execute_trade_pipeline(decision_dict, market_event)
                    results["trade_execution"] = trade_result
                except Exception as e:
                    error_msg = f"Error in trade execution pipeline: {str(e)}"
                    self.logger.error(error_msg)
                    self.logger.error(f"Stack trace: {traceback.format_exc()}")
                    
                    # Store error in results
                    results["trade_execution"] = {
                        "status": "error",
                        "error": True,
                        "message": error_msg,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
            
            return results
        
        except Exception as e:
            # Handle any unexpected errors in the workflow
            error_msg = f"Unexpected error in analysis workflow: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(f"Stack trace: {traceback.format_exc()}")
            
            # Return error results
            return {
                "error": True,
                "message": error_msg,
                "symbol": results.get("symbol", self.default_symbol),
                "interval": results.get("interval", self.default_interval),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "analyses": results.get("analyses", {}),
                "decision": {
                    "action": "HOLD",
                    "pair": results.get("symbol", self.default_symbol),
                    "confidence": 0,
                    "reason": f"Workflow error: {str(e)}",
                    "decision_method": "error_fallback"
                }
            }
    
    @handle_trade_execution_error
    def _execute_trade_pipeline(self, 
                             decision: Dict[str, Any], 
                             market_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the trade decision through the trade execution pipeline.
        
        Args:
            decision: Trading decision dictionary
            market_data: Optional market data for risk assessment
            
        Returns:
            Dictionary with trade execution results
        """
        try:
            # Validate input trade decision before proceeding
            if not isinstance(decision, dict):
                raise ValidationError(f"Invalid decision format: expected dict, got {type(decision)}")
                
            required_fields = ["action", "pair", "confidence"]
            for field in required_fields:
                if field not in decision:
                    raise ValidationError(f"Missing required field in decision: {field}")
                    
            # Validate action type
            if decision.get("action") not in ["BUY", "SELL", "HOLD"]:
                raise ValidationError(f"Invalid action in decision: {decision.get('action')}")
                
            self.logger.info(f"Starting trade execution pipeline for {decision.get('action')} {decision.get('pair')}")
            
            # Initialize the result dictionary
            result = {
                "status": "initiated",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "decision": decision,
                "pipeline_steps": [],
                "trade_id": None
            }
            
            # Create a mock trade from the decision for use throughout the pipeline
            mock_trade = {
                "pair": decision.get("pair"),
                "action": decision.get("action"),
                "confidence": decision.get("confidence", 0),
                "entry_price": 0.0,  # Will be populated by TradeExecutor if approved
                "position_size": 0.0  # Will be determined by PositionSizer if approved
            }
            
            # Step 1: Portfolio validation
            if "portfolio_manager" in self.agents:
                self.logger.info("Step 1: Portfolio validation")
                try:
                    portfolio_manager = self.agents["portfolio_manager"]
                    
                    # Validate the trade against portfolio limits
                    portfolio_validation = portfolio_manager.validate_trade(mock_trade)
                    
                    # Add to pipeline steps
                    result["pipeline_steps"].append({
                        "step": "portfolio_validation",
                        "status": portfolio_validation.get("status"),
                        "reason": portfolio_validation.get("reason"),
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
                    # Check if trade was rejected
                    if portfolio_validation.get("status") == TradeValidationStatus.REJECTED.value:
                        self.logger.warning(f"Trade rejected by Portfolio Manager: {portfolio_validation.get('reason')}")
                        result["status"] = "rejected_by_portfolio_manager"
                        result["reason"] = portfolio_validation.get("reason")
                        return result
                        
                    self.logger.info(f"Portfolio validation passed: {portfolio_validation.get('reason')}")
                except Exception as e:
                    error_msg = f"Portfolio validation error: {str(e)}"
                    self.logger.error(error_msg)
                    self.logger.error(f"Stack trace: {traceback.format_exc()}")
                    
                    result["pipeline_steps"].append({
                        "step": "portfolio_validation",
                        "status": "error",
                        "reason": error_msg,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
                    result["status"] = "error_in_portfolio_validation"
                    result["reason"] = error_msg
                    return result
            
            # Step 2: Risk guard assessment
            if "risk_guard" in self.agents:
                self.logger.info("Step 2: Risk assessment")
                try:
                    risk_guard = self.agents["risk_guard"]
                    
                    # Evaluate trade risk
                    risk_assessment = risk_guard.evaluate_trade_risk(mock_trade, market_data)
                    
                    # Add to pipeline steps
                    result["pipeline_steps"].append({
                        "step": "risk_assessment",
                        "status": risk_assessment.get("status"),
                        "reason": risk_assessment.get("reason"),
                        "metrics": risk_assessment.get("risk_metrics", {}),
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
                    # Check if trade was rejected
                    if risk_assessment.get("status") == RiskApprovalStatus.REJECTED.value:
                        self.logger.warning(f"Trade rejected by Risk Guard: {risk_assessment.get('reason')}")
                        result["status"] = "rejected_by_risk_guard"
                        result["reason"] = risk_assessment.get("reason")
                        return result
                        
                    self.logger.info(f"Risk assessment passed: {risk_assessment.get('reason')}")
                except Exception as e:
                    error_msg = f"Risk assessment error: {str(e)}"
                    self.logger.error(error_msg)
                    self.logger.error(f"Stack trace: {traceback.format_exc()}")
                    
                    result["pipeline_steps"].append({
                        "step": "risk_assessment",
                        "status": "error",
                        "reason": error_msg,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
                    result["status"] = "error_in_risk_assessment"
                    result["reason"] = error_msg
                    return result
            
            # Step 3: Position sizing
            if "position_sizer" in self.agents:
                self.logger.info("Step 3: Position sizing")
                try:
                    position_sizer = self.agents["position_sizer"]
                    
                    # Calculate position size
                    position_data = position_sizer.calculate_position_size(decision, market_data)
                    
                    # Validate position size data
                    if "position_size_usdt" not in position_data:
                        raise ValidationError("Position sizer did not return a valid position size")
                        
                    # Add to pipeline steps
                    result["pipeline_steps"].append({
                        "step": "position_sizing",
                        "status": "completed",
                        "position_size_usdt": position_data.get("position_size_usdt", 0),
                        "asset_quantity": position_data.get("asset_quantity", 0),
                        "confidence_factor": position_data.get("confidence_factor", 0),
                        "volatility_factor": position_data.get("volatility_factor", 0),
                        "volatility_pct": position_data.get("volatility_pct", 0),
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
                    # Update the mock trade with position size
                    mock_trade["position_size"] = position_data.get("position_size_usdt", 0)
                    
                    # Update the decision with position size for trade execution
                    decision["position_size"] = position_data.get("position_size_usdt", 0)
                    
                    self.logger.info(f"Position sizing completed: {position_data.get('position_size_usdt', 0)} USDT")
                except Exception as e:
                    error_msg = f"Position sizing error: {str(e)}"
                    self.logger.error(error_msg)
                    self.logger.error(f"Stack trace: {traceback.format_exc()}")
                    
                    result["pipeline_steps"].append({
                        "step": "position_sizing",
                        "status": "error",
                        "reason": error_msg,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
                    result["status"] = "error_in_position_sizing"
                    result["reason"] = error_msg
                    return result
            
            # Step 4: Trade execution
            if "trade_executor" in self.agents:
                self.logger.info("Step 4: Trade execution")
                try:
                    trade_executor = self.agents["trade_executor"]
                    
                    # Execute the trade
                    trade_result = trade_executor.process_decision(decision, market_data)
                    
                    # Add to pipeline steps
                    result["pipeline_steps"].append({
                        "step": "trade_execution",
                        "status": trade_result.get("status", "unknown"),
                        "message": trade_result.get("message", ""),
                        "trade_id": trade_result.get("trade_id"),
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
                    # Update the overall status
                    result["status"] = trade_result.get("status", "unknown")
                    result["trade_id"] = trade_result.get("trade_id")
                    
                    if trade_result.get("status") == "success":
                        self.logger.info(f"Trade executed successfully: {trade_result.get('trade_id')}")
                    else:
                        self.logger.warning(f"Trade execution issue: {trade_result.get('message')}")
                except Exception as e:
                    error_msg = f"Trade execution error: {str(e)}"
                    self.logger.error(error_msg)
                    self.logger.error(f"Stack trace: {traceback.format_exc()}")
                    
                    result["pipeline_steps"].append({
                        "step": "trade_execution",
                        "status": "error",
                        "reason": error_msg,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
                    result["status"] = "error_in_trade_execution"
                    result["reason"] = error_msg
            
            # Final status and logging
            self.logger.info(f"Trade pipeline completed with status: {result['status']}")
            
            return result
            
        except ValidationError as e:
            # Handle validation errors
            self.logger.error(f"Validation error in trade pipeline: {str(e)}")
            self.logger.error(f"Stack trace: {traceback.format_exc()}")
            
            # Return error result
            return {
                "status": "error_validation",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "reason": str(e),
                "pipeline_steps": [{
                    "step": "validation",
                    "status": "error",
                    "reason": str(e),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }]
            }
        except Exception as e:
            # Handle unexpected errors
            self.logger.error(f"Unexpected error in trade pipeline: {str(e)}")
            self.logger.error(f"Stack trace: {traceback.format_exc()}")
            
            # Return error result
            return {
                "status": "error_unexpected",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "reason": str(e),
                "pipeline_steps": [{
                    "step": "unknown",
                    "status": "error",
                    "reason": str(e),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }]
            }
    
    def save_results(self, results: Dict[str, Any], filepath: Optional[str] = None) -> str:
        """
        Save analysis results to a file.
        
        Args:
            results: Analysis results dictionary
            filepath: Output filepath (optional)
            
        Returns:
            Path to the saved file
        """
        # Create default filepath if not provided
        if not filepath:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            symbol = results.get("symbol", "unknown").replace("/", "")
            filepath = os.path.join(parent_dir, f"logs/decisions/{symbol}_{timestamp}.json")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Save results
        try:
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2)
            self.logger.info(f"Results saved to {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"Error saving results: {e}")
            return ""

# Example usage (for demonstration)
if __name__ == "__main__":
    # Create orchestrator
    orchestrator = CoreOrchestrator()
    
    # Run analysis
    results = orchestrator.run_analysis("BTC/USDT", "1h")
    
    # Save results
    output_path = orchestrator.save_results(results)
    
    # Print decision
    if "decision" in results and results["decision"]:
        print("\nTrading Decision:")
        print(f"Action: {results['decision']['action']}")
        print(f"Pair: {results['decision']['pair']}")
        print(f"Confidence: {results['decision']['confidence']}")
        print(f"Reason: {results['decision']['reason']}")
        
        # Print trade execution result if available
        if "trade_execution" in results:
            execution = results["trade_execution"]
            print("\nTrade Execution:")
            print(f"Status: {execution.get('status', 'unknown')}")
            
            # Print each pipeline step
            if "pipeline_steps" in execution:
                print("\nExecution Pipeline:")
                for step in execution["pipeline_steps"]:
                    status = step.get("status", "unknown")
                    emoji = "✅" if status in ["approved", "completed", "success"] else "❌" if status in ["rejected", "error"] else "⚠️"
                    print(f"{emoji} {step['step']}: {status} - {step.get('reason', '')}")
                    
            # Print trade ID if successful
            if execution.get("status") == "success" and execution.get("trade_id"):
                print(f"\nTrade ID: {execution['trade_id']}")
                
        print(f"\nFull results saved to: {output_path}")