"""
Risk-Based Decision Agent Test

Tests the integration of the risk analysis and portfolio management agents
into the AutoGen-based collaborative decision process.
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("risk_decision_test")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Risk-Based Decision Agent Test")
    
    parser.add_argument("--symbol", type=str, default="BTCUSDT",
                      help="Trading symbol to analyze")
    parser.add_argument("--risk_tolerance", type=float, default=0.02,
                      help="Risk tolerance as percentage of portfolio (default: 0.02 = 2%%)")
    parser.add_argument("--initial_balance", type=float, default=10000.0,
                      help="Initial account balance for backtesting")
    parser.add_argument("--output_dir", type=str, default="data/risk_agent_test",
                      help="Directory for test output")
    parser.add_argument("--max_turns", type=int, default=10,
                      help="Maximum number of conversation turns")
    
    return parser.parse_args()

def check_openai_api_key() -> bool:
    """Check if OpenAI API key is available"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable not set")
        return False
    return True

def setup_agent_system(symbol: str, risk_tolerance: float, initial_balance: float):
    """Set up the agent system with risk management components"""
    try:
        import autogen
        from agents.portfolio_management import (
            risk_analysis_agent_definition, 
            portfolio_manager_agent_definition
        )
        
        # Set up OpenAI config
        openai_config = {
            "config_list": [
                {
                    "model": "gpt-4o",
                    "api_key": os.environ.get("OPENAI_API_KEY"),
                }
            ],
            "timeout": 120,
        }
        
        # Create a simulated portfolio for the test
        from agents.database_retrieval_tool import get_latest_market_data
        
        current_price = 0
        try:
            market_data = get_latest_market_data(symbol=symbol)
            if market_data and "close" in market_data:
                current_price = float(market_data["close"])
        except Exception as e:
            logger.warning(f"Could not get market price: {str(e)}")
            current_price = 60000 if symbol == "BTCUSDT" else 3000
        
        # Create a basic portfolio (70% cash, 30% in the target symbol)
        if current_price <= 0:
            current_price = 60000 if symbol == "BTCUSDT" else 3000
        
        symbol_allocation = 0.3  # 30% allocation to the symbol
        quantity = (initial_balance * symbol_allocation) / current_price
        
        portfolio = {
            "cash_balance": initial_balance * (1 - symbol_allocation),
            "positions": [
                {
                    "symbol": symbol,
                    "quantity": quantity,
                    "avg_price": current_price * 0.95,  # Simulated entry 5% lower
                    "current_price": current_price,
                    "value": (initial_balance * symbol_allocation)
                }
            ],
            "total_equity": initial_balance
        }
        
        # Get the agent definitions
        risk_agent_def = risk_analysis_agent_definition()
        portfolio_agent_def = portfolio_manager_agent_definition()
        
        # Register the risk analysis functions
        def calculate_value_at_risk(symbol: str, position_value: float, 
                                  lookback_days: int = 30, interval: str = "1h") -> Dict[str, Any]:
            """Calculate Value at Risk (VaR) for a position"""
            from agents.portfolio_management import RiskAnalyzer
            analyzer = RiskAnalyzer()
            return analyzer.calculate_value_at_risk(
                symbol=symbol, 
                position_value=position_value,
                lookback_days=lookback_days,
                interval=interval
            )
            
        def calculate_max_position_size(symbol: str, entry_price: float, stop_loss: float, 
                                      portfolio_value: float) -> Dict[str, Any]:
            """Calculate maximum position size based on risk parameters"""
            from agents.portfolio_management import RiskAnalyzer
            analyzer = RiskAnalyzer(risk_tolerance=risk_tolerance)
            return analyzer.calculate_max_position_size(
                symbol=symbol,
                entry_price=entry_price,
                stop_loss=stop_loss,
                portfolio_value=portfolio_value
            )
            
        def calculate_kelly_position_size(win_rate: float, risk_reward_ratio: float, 
                                         portfolio_value: float) -> Dict[str, Any]:
            """Calculate position size using the Kelly Criterion"""
            from agents.portfolio_management import RiskAnalyzer
            analyzer = RiskAnalyzer(risk_tolerance=risk_tolerance)
            return analyzer.calculate_kelly_position_size(
                win_rate=win_rate,
                risk_reward_ratio=risk_reward_ratio,
                portfolio_value=portfolio_value
            )
            
        def calculate_volatility_adjusted_size(symbol: str, portfolio_value: float, 
                                             lookback_days: int = 30, 
                                             target_volatility: float = 0.01) -> Dict[str, Any]:
            """Calculate volatility-adjusted position size"""
            from agents.portfolio_management import RiskAnalyzer
            analyzer = RiskAnalyzer(risk_tolerance=risk_tolerance)
            return analyzer.calculate_volatility_adjusted_size(
                symbol=symbol,
                portfolio_value=portfolio_value,
                lookback_days=lookback_days,
                target_volatility=target_volatility
            )
            
        def analyze_portfolio_risk(portfolio: Dict[str, Any]) -> Dict[str, Any]:
            """Analyze overall portfolio risk metrics"""
            from agents.portfolio_management import RiskAnalyzer
            analyzer = RiskAnalyzer(risk_tolerance=risk_tolerance)
            return analyzer.analyze_portfolio_risk(portfolio)
            
        def get_optimal_position_size(symbol: str, entry_price: float, stop_loss: float,
                                    portfolio: Dict[str, Any], win_probability: float = 0.5, 
                                    risk_reward_ratio: float = 1.5) -> Dict[str, Any]:
            """Calculate optimal position size using multiple techniques"""
            from agents.portfolio_management import PortfolioManager
            manager = PortfolioManager(risk_tolerance=risk_tolerance)
            return manager.get_optimal_position_size(
                symbol=symbol,
                entry_price=entry_price,
                stop_loss=stop_loss,
                portfolio=portfolio,
                win_probability=win_probability,
                risk_reward_ratio=risk_reward_ratio
            )
            
        def get_position_adjustment(symbol: str, current_price: float, current_position: Dict[str, Any], 
                                   portfolio: Dict[str, Any], target_allocation: float = None) -> Dict[str, Any]:
            """Calculate position size adjustment based on current position and target allocation"""
            from agents.portfolio_management import PortfolioManager
            manager = PortfolioManager(risk_tolerance=risk_tolerance)
            return manager.get_position_adjustment(
                symbol=symbol,
                current_price=current_price,
                current_position=current_position,
                portfolio=portfolio,
                target_allocation=target_allocation
            )
            
        def optimize_portfolio(portfolio: Dict[str, Any], risk_profile: str = "moderate") -> Dict[str, Any]:
            """Optimize portfolio allocations based on risk profile"""
            from agents.portfolio_management import PortfolioManager
            manager = PortfolioManager(risk_tolerance=risk_tolerance)
            return manager.optimize_portfolio(
                portfolio=portfolio,
                risk_profile=risk_profile
            )
        
        # Create configuration for database functions
        from agents.database_retrieval_tool import (
            get_latest_market_data,
            get_recent_market_data,
            get_price_history,
            calculate_volatility,
            calculate_rsi
        )
        
        # Create the function map
        function_map = {
            "get_latest_market_data": get_latest_market_data,
            "get_recent_market_data": get_recent_market_data,
            "get_price_history": get_price_history,
            "calculate_volatility": calculate_volatility,
            "calculate_rsi": calculate_rsi,
            "calculate_value_at_risk": calculate_value_at_risk,
            "calculate_max_position_size": calculate_max_position_size,
            "calculate_kelly_position_size": calculate_kelly_position_size,
            "calculate_volatility_adjusted_size": calculate_volatility_adjusted_size,
            "analyze_portfolio_risk": analyze_portfolio_risk,
            "get_optimal_position_size": get_optimal_position_size,
            "get_position_adjustment": get_position_adjustment,
            "optimize_portfolio": optimize_portfolio
        }
        
        # Create agents
        analyst_agent = autogen.AssistantAgent(
            name="MarketAnalystAgent",
            system_message="""You are a Market Analyst Agent specializing in cryptocurrency 
technical and fundamental analysis. Your role is to analyze market data, identify patterns, and 
provide objective assessments of market conditions.

You should evaluate:
1. Market trends (bullish, bearish, or neutral)
2. Technical indicators (RSI, volatility, etc.)
3. Important support and resistance levels
4. Recent price action and volume patterns

You can use technical indicators from the database system via function calls. 
Always base your analysis on actual data, not guesses.""",
            llm_config={
                "config_list": openai_config["config_list"],
                "functions": [
                    {
                        "name": "get_latest_market_data",
                        "description": "Get the latest market data for a trading symbol",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "symbol": {
                                    "type": "string",
                                    "description": "Trading symbol (e.g., BTCUSDT)"
                                }
                            },
                            "required": ["symbol"]
                        }
                    },
                    {
                        "name": "get_recent_market_data",
                        "description": "Get recent market data for a trading symbol",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "symbol": {
                                    "type": "string",
                                    "description": "Trading symbol (e.g., BTCUSDT)"
                                },
                                "limit": {
                                    "type": "integer",
                                    "description": "Number of recent data points to retrieve"
                                },
                                "interval": {
                                    "type": "string",
                                    "description": "Time interval for the data points (e.g., 1h, 4h, 1d)"
                                }
                            },
                            "required": ["symbol"]
                        }
                    },
                    {
                        "name": "calculate_rsi",
                        "description": "Calculate the Relative Strength Index (RSI) for a trading symbol",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "symbol": {
                                    "type": "string",
                                    "description": "Trading symbol (e.g., BTCUSDT)"
                                },
                                "interval": {
                                    "type": "string",
                                    "description": "Time interval for the data points (e.g., 1h, 4h, 1d)",
                                    "default": "1h"
                                },
                                "period": {
                                    "type": "integer",
                                    "description": "Period for RSI calculation",
                                    "default": 14
                                }
                            },
                            "required": ["symbol"]
                        }
                    }
                ]
            }
        )
        
        risk_analyst_agent = autogen.AssistantAgent(
            name="RiskAnalysisAgent",
            system_message=risk_agent_def["system_message"],
            llm_config={
                "config_list": openai_config["config_list"],
                "functions": risk_agent_def["functions"]
            }
        )
        
        portfolio_manager_agent = autogen.AssistantAgent(
            name="PortfolioManagerAgent",
            system_message=portfolio_agent_def["system_message"],
            llm_config={
                "config_list": openai_config["config_list"],
                "functions": portfolio_agent_def["functions"]
            }
        )
        
        strategist_agent = autogen.AssistantAgent(
            name="StrategyAgent",
            system_message="""You are a Trading Strategy Agent responsible for making the final trading 
decision based on inputs from market analysis, risk assessment, and portfolio management.

Your role is to:
1. Evaluate technical and fundamental analysis from the Market Analyst
2. Consider position sizing and risk parameters from the Risk Analyst
3. Review portfolio optimization recommendations from the Portfolio Manager
4. Formulate a clear trading decision with specific parameters

Your output should be a trading decision including:
- Symbol: The trading pair to act on
- Action: Buy, Sell, or Hold
- Entry price: Recommended entry price
- Stop loss: Where to place the stop loss
- Take profit: Target price for taking profits
- Position size: Amount to trade (as provided by risk analysis)
- Confidence: Level of confidence in this decision (0-100%)
- Rationale: Brief explanation of your decision""",
            llm_config={
                "config_list": openai_config["config_list"]
            }
        )
        
        user_proxy = autogen.UserProxyAgent(
            name="UserProxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            is_termination_msg=lambda x: "FINAL DECISION" in x.get("content", ""),
            code_execution_config=False,
            function_map=function_map
        )
        
        # Create group chat
        groupchat = autogen.GroupChat(
            agents=[user_proxy, analyst_agent, risk_analyst_agent, portfolio_manager_agent, strategist_agent],
            messages=[],
            max_round=20
        )
        
        group_chat_manager = autogen.GroupChatManager(
            groupchat=groupchat,
            llm_config={"config_list": openai_config["config_list"]}
        )
        
        return {
            "user_proxy": user_proxy,
            "market_analyst": analyst_agent,
            "risk_analyst": risk_analyst_agent,
            "portfolio_manager": portfolio_manager_agent,
            "strategist": strategist_agent,
            "group_chat_manager": group_chat_manager,
            "portfolio": portfolio,
            "function_map": function_map
        }
    
    except Exception as e:
        logger.error(f"Error setting up agent system: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def run_risk_based_decision(args):
    """Run the risk-based decision making session"""
    # Set up the agent system
    agent_system = setup_agent_system(
        symbol=args.symbol,
        risk_tolerance=args.risk_tolerance,
        initial_balance=args.initial_balance
    )
    
    if not agent_system:
        logger.error("Failed to set up agent system")
        return None
    
    # Prepare the initial message with portfolio information
    portfolio = agent_system["portfolio"]
    portfolio_info = f"""
Current Portfolio Information:
- Total Equity: ${portfolio['total_equity']}
- Cash Balance: ${portfolio['cash_balance']}
- Positions:
"""
    
    for position in portfolio["positions"]:
        portfolio_info += f"  * {position['symbol']}: {position['quantity']} @ ${position['avg_price']} (Value: ${position['value']})\n"
    
    # Construct the initial prompt
    initial_prompt = f"""
I need a complete trading analysis and risk-managed decision for {args.symbol}.

{portfolio_info}

Please work collaboratively to:
1. Perform technical analysis of {args.symbol} using recent market data
2. Analyze portfolio risk with the current position allocation
3. Calculate optimal position size for a potential new trade with {args.risk_tolerance*100}% risk tolerance
4. Provide a clear trading decision (Buy, Sell, or Hold) with:
   - Specific entry price
   - Stop loss level
   - Take profit target
   - Position size recommendation
   - Confidence level

Market Analyst: Begin with technical analysis of {args.symbol}, including price trends, RSI, and volatility.
Risk Analyst: Then analyze the risk parameters for a potential trade.
Portfolio Manager: Next, evaluate the portfolio allocation and recommend position sizing.
Strategy Agent: Finally, use all this information to provide the FINAL DECISION.
"""
    
    # Start the conversation
    user_proxy = agent_system["user_proxy"]
    group_chat_manager = agent_system["group_chat_manager"]
    
    # Initiate the chat
    user_proxy.initiate_chat(group_chat_manager, message=initial_prompt)
    
    # Extract the final decision from the chat history
    messages = group_chat_manager.groupchat.messages
    final_decision = None
    
    for message in reversed(messages):
        if "FINAL DECISION" in message.get("content", ""):
            final_decision = message
            break
    
    # Parse the decision
    if final_decision:
        decision_content = final_decision.get("content", "")
        
        # Try to extract decision parameters
        import re
        
        decision_params = {}
        
        # Extract symbol
        symbol_match = re.search(r"Symbol:\s*([A-Z]+/[A-Z]+|[A-Z]+)", decision_content)
        if symbol_match:
            decision_params["symbol"] = symbol_match.group(1)
        
        # Extract action
        action_match = re.search(r"Action:\s*(Buy|Sell|Hold)", decision_content, re.IGNORECASE)
        if action_match:
            decision_params["action"] = action_match.group(1).lower()
        
        # Extract entry price
        entry_match = re.search(r"Entry\s*[Pp]rice:\s*\$?([\d,.]+)", decision_content)
        if entry_match:
            decision_params["entry_price"] = float(entry_match.group(1).replace(",", ""))
        
        # Extract stop loss
        sl_match = re.search(r"Stop\s*[Ll]oss:\s*\$?([\d,.]+)", decision_content)
        if sl_match:
            decision_params["stop_loss"] = float(sl_match.group(1).replace(",", ""))
        
        # Extract take profit
        tp_match = re.search(r"Take\s*[Pp]rofit:\s*\$?([\d,.]+)", decision_content)
        if tp_match:
            decision_params["take_profit"] = float(tp_match.group(1).replace(",", ""))
        
        # Extract position size
        size_match = re.search(r"Position\s*[Ss]ize:\s*\$?([\d,.]+)", decision_content)
        if size_match:
            decision_params["position_size"] = float(size_match.group(1).replace(",", ""))
        
        # Extract confidence
        conf_match = re.search(r"Confidence:\s*(\d+)%", decision_content)
        if conf_match:
            decision_params["confidence"] = float(conf_match.group(1)) / 100.0
        
        # Extract rationale
        rationale_match = re.search(r"Rationale:(.*?)(?:\n\n|\Z)", decision_content, re.DOTALL)
        if rationale_match:
            decision_params["rationale"] = rationale_match.group(1).strip()
        
        # Return the complete result
        return {
            "messages": messages,
            "final_decision": final_decision,
            "decision_params": decision_params
        }
    
    return {
        "messages": messages,
        "final_decision": None,
        "decision_params": None,
        "error": "No final decision found in conversation"
    }

def test_paper_trade_execution(decision_params, args):
    """Test executing the decision in the paper trading system"""
    if not decision_params or "action" not in decision_params:
        logger.error("Invalid decision parameters")
        return None
    
    from agents.paper_trading import PaperTradingSystem
    from orchestration.risk_optimizer import RiskOptimizer
    
    # Create trading system
    trading_system = PaperTradingSystem(data_dir=args.output_dir)
    
    # Create test account
    account = trading_system.create_account(
        account_id=f"decision_test_{int(datetime.now().timestamp())}",
        initial_balance=args.initial_balance
    )
    
    # Get initial portfolio
    initial_portfolio = trading_system.get_portfolio(account.account_id)
    
    # Execute the decision
    execution_result = trading_system.execute_from_decision(
        decision=decision_params,
        account_id=account.account_id,
        use_risk_optimizer=True
    )
    
    # Get updated portfolio
    final_portfolio = trading_system.get_portfolio(account.account_id)
    
    return {
        "initial_portfolio": initial_portfolio,
        "execution_result": execution_result,
        "final_portfolio": final_portfolio
    }

def main():
    """Main entry point"""
    args = parse_arguments()
    
    print("\n" + "=" * 80)
    print(f" Risk-Based Decision Agent Test for {args.symbol} ".center(80, "="))
    print("=" * 80 + "\n")
    
    # Check for OpenAI API key
    if not check_openai_api_key():
        logger.error("OpenAI API key is required for this test.")
        sys.exit(1)
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Define output file path
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(args.output_dir, f"risk_decision_test_{timestamp}.json")
    
    try:
        # Run the risk-based decision process
        print("Running risk-based decision process...")
        print(f"Symbol: {args.symbol}")
        print(f"Risk tolerance: {args.risk_tolerance*100:.1f}%")
        print(f"Initial balance: ${args.initial_balance}\n")
        
        decision_result = run_risk_based_decision(args)
        
        if not decision_result or not decision_result.get("final_decision"):
            print("\nNo final decision was reached.")
            if decision_result and "error" in decision_result:
                print(f"Error: {decision_result['error']}")
            sys.exit(1)
        
        # Display the decision
        decision_params = decision_result.get("decision_params", {})
        
        print("\n" + "=" * 50)
        print(" TRADING DECISION ")
        print("=" * 50)
        
        print(f"Symbol: {decision_params.get('symbol', args.symbol)}")
        print(f"Action: {decision_params.get('action', 'Unknown')}")
        
        if "entry_price" in decision_params:
            print(f"Entry Price: ${decision_params['entry_price']:.2f}")
        
        if "stop_loss" in decision_params:
            print(f"Stop Loss: ${decision_params['stop_loss']:.2f}")
        
        if "take_profit" in decision_params:
            print(f"Take Profit: ${decision_params['take_profit']:.2f}")
        
        if "position_size" in decision_params:
            print(f"Position Size: ${decision_params['position_size']:.2f}")
        
        if "confidence" in decision_params:
            print(f"Confidence: {decision_params['confidence']*100:.1f}%")
        
        if "rationale" in decision_params:
            print("\nRationale:")
            print(decision_params['rationale'])
        
        print("\n" + "=" * 50)
        
        # Execute the decision in the paper trading system
        print("\nExecuting decision in paper trading system...")
        execution_result = test_paper_trade_execution(decision_params, args)
        
        if execution_result:
            # Display execution results
            print("\nExecution Result:")
            if "execution_result" in execution_result:
                result = execution_result["execution_result"]
                print(f"Status: {result.get('status', 'Unknown')}")
                print(f"Message: {result.get('message', 'No message')}")
                
                # Show portfolio change
                if "initial_portfolio" in execution_result and "final_portfolio" in execution_result:
                    initial = execution_result["initial_portfolio"]
                    final = execution_result["final_portfolio"]
                    
                    print("\nPortfolio Change:")
                    print(f"Initial Equity: ${initial.get('total_equity', 0):.2f}")
                    print(f"Final Equity: ${final.get('total_equity', 0):.2f}")
                    
                    # Show positions
                    if "positions" in final and final["positions"]:
                        print("\nCurrent Positions:")
                        for pos in final["positions"]:
                            print(f"  {pos['symbol']}: {pos['quantity']:.6f} @ ${pos['avg_price']:.2f} (Value: ${pos['value']:.2f})")
        
        # Save results to file
        result_data = {
            "timestamp": timestamp,
            "symbol": args.symbol,
            "risk_tolerance": args.risk_tolerance,
            "initial_balance": args.initial_balance,
            "decision_result": decision_params,
            "execution_result": execution_result,
            "conversation": decision_result.get("messages", [])
        }
        
        with open(output_file, "w") as f:
            json.dump(result_data, f, indent=2, default=str)
        
        print(f"\nTest results saved to: {output_file}")
        print("\nRisk-based decision agent test completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in test: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        print(f"\nTest failed with error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()