"""
Database Query Agent for AutoGen

This module implements a database query agent for AutoGen that provides
market data and analytics to other agents in a multi-agent system.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union, Callable

# Import the database integration module
from agents.database_integration import AgentDatabaseInterface

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("database_query_agent")

def register_with_autogen(agents_config: Dict[str, Any]) -> None:
    """
    Register database query functions with AutoGen agents.
    
    This function registers database query capabilities with AutoGen agents,
    allowing them to access market data directly through function calls
    during agent conversations.
    
    Args:
        agents_config: Dictionary of agent configurations
        
    Examples:
        ```python
        # Configure agents
        agents_config = {
            "market_analyst": {
                "name": "MarketAnalyst",
                "system_message": "You are an expert cryptocurrency market analyst...",
                "llm_config": {
                    "config_list": config_list,
                    "temperature": 0.2,
                }
            },
            # ... other agents
        }
        
        # Register database functions with AutoGen
        register_with_autogen(agents_config)
        ```
    """
    try:
        # Import AutoGen components for registration
        try:
            from autogen import register_function, ConversableAgent
        except ImportError:
            logger.error("AutoGen package not found. Please install with 'pip install pyautogen'")
            return
        
        # Create a database query agent instance for function access
        db_agent = DatabaseQueryAgent()
        
        # Define wrapper functions that will be registered with AutoGen
        def query_market_data(symbol: str, interval: str = '1h', limit: int = 24, 
                             days: Optional[int] = None, format_type: str = 'json') -> str:
            """
            Query market data for a specific symbol.
            
            Args:
                symbol: Trading symbol (e.g., 'BTCUSDT')
                interval: Time interval (e.g., '1m', '5m', '15m', '1h', '4h', '1d')
                limit: Number of data points to retrieve
                days: Number of days to look back (alternative to limit)
                format_type: Output format ('json', 'markdown', 'text')
                
            Returns:
                Formatted market data
            """
            return db_agent.query_market_data(symbol, interval, limit, days, format_type)
        
        def get_market_statistics(symbol: str, interval: str = '1d', 
                                 days: int = 30, format_type: str = 'json') -> str:
            """
            Get market statistics for a specific symbol.
            
            Args:
                symbol: Trading symbol (e.g., 'BTCUSDT')
                interval: Time interval (e.g., '1h', '4h', '1d')
                days: Number of days to look back
                format_type: Output format ('json', 'markdown', 'text')
                
            Returns:
                Formatted market statistics
            """
            return db_agent.get_market_statistics(symbol, interval, days, format_type)
        
        def query_funding_rates(symbol: str, days: int = 7, format_type: str = 'json') -> str:
            """
            Query funding rates for a specific symbol.
            
            Args:
                symbol: Trading symbol (e.g., 'BTCUSDT')
                days: Number of days to look back
                format_type: Output format ('json', 'markdown', 'text')
                
            Returns:
                Formatted funding rate data
            """
            return db_agent.query_funding_rates(symbol, days, format_type)
        
        def query_exchange_flows(symbol: str, days: int = 7, format_type: str = 'json') -> str:
            """
            Query exchange flows for a specific symbol.
            
            Args:
                symbol: Trading symbol (e.g., 'BTC')
                days: Number of days to look back
                format_type: Output format ('json', 'markdown', 'text')
                
            Returns:
                Formatted exchange flow data
            """
            return db_agent.query_exchange_flows(symbol, days, format_type)
        
        def general_database_query(query: str) -> str:
            """
            Execute a general database query.
            
            Args:
                query: Natural language query to process
                
            Returns:
                Query results
            """
            return db_agent.process_message(query)
        
        # Register functions with each agent that has llm_config
        for agent_id, agent_config in agents_config.items():
            if "llm_config" in agent_config:
                logger.info(f"Registering database functions with agent: {agent_id}")
                
                # Create the agent if it doesn't exist yet
                if isinstance(agent_config, dict) and not isinstance(agent_config, ConversableAgent):
                    # The agent will be created later, register the functions to the config
                    if "function_map" not in agent_config["llm_config"]:
                        agent_config["llm_config"]["function_map"] = {}
                    
                    # Add our database functions to the function map
                    function_map = agent_config["llm_config"]["function_map"]
                    function_map["query_market_data"] = query_market_data
                    function_map["get_market_statistics"] = get_market_statistics
                    function_map["query_funding_rates"] = query_funding_rates
                    function_map["query_exchange_flows"] = query_exchange_flows
                    function_map["general_database_query"] = general_database_query
                else:
                    # The agent already exists, register functions directly through function_map
                    if hasattr(agent_config, 'register_function'):
                        agent_config.register_function(
                            function_map={
                                "query_market_data": query_market_data,
                                "get_market_statistics": get_market_statistics,
                                "query_funding_rates": query_funding_rates,
                                "query_exchange_flows": query_exchange_flows,
                                "general_database_query": general_database_query
                            }
                        )
                    else:
                        logger.warning(f"Agent {agent_id} does not support function registration")
        
        logger.info("Successfully registered database functions with AutoGen agents")
    
    except Exception as e:
        logger.error(f"Error registering database functions with AutoGen: {str(e)}")
        raise

class DatabaseQueryAgent:
    """
    Database Query Agent for AutoGen
    
    This agent provides a structured interface for other agents to retrieve
    market data and analytics from the database.
    """
    
    def __init__(self, agent_name: str = "DatabaseQueryAgent"):
        """
        Initialize the database query agent
        
        Args:
            agent_name: Name of the agent
        """
        self.name = agent_name
        self.db_interface = AgentDatabaseInterface()
        self.request_count = 0
        self.last_query = None
        self.last_response = None
        logger.info(f"{self.name} initialized")
    
    def process_message(self, message: str) -> str:
        """
        Process a message from another agent
        
        Args:
            message: Message content from an agent
            
        Returns:
            Response message
        """
        try:
            # Track requests
            self.request_count += 1
            self.last_query = message
            
            # Parse the message to extract query parameters
            query_type, params = self._parse_query(message)
            
            # Process different query types
            if query_type == "market_data":
                response = self._get_market_data(params)
            elif query_type == "technical_analysis":
                response = self._get_technical_analysis(params)
            elif query_type == "price":
                response = self._get_price_data(params)
            elif query_type == "volatility":
                response = self._get_volatility(params)
            elif query_type == "support_resistance":
                response = self._get_support_resistance(params)
            elif query_type == "market_summary":
                response = self._get_market_summary(params)
            elif query_type == "available_symbols":
                response = self._get_available_symbols()
            elif query_type == "available_intervals":
                response = self._get_available_intervals(params)
            elif query_type == "help":
                response = self._get_help()
            else:
                # Process as a general query
                response = self._process_general_query(message, params)
            
            # Track response
            self.last_response = response
            
            return response
        
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}\n\nPlease try a different query format or check the 'help' command for guidance."
    
    def _parse_query(self, message: str) -> Tuple[str, Dict[str, Any]]:
        """
        Parse a query message to extract query type and parameters
        
        Args:
            message: Message content from an agent
            
        Returns:
            Tuple of (query_type, parameters)
        """
        # Default parameters
        params = {
            "symbol": "BTCUSDT",
            "interval": "1h",
            "days": 7,
            "limit": 20
        }
        
        # Ensure numeric params are integers
        for key in ["days", "limit"]:
            if key in params and not isinstance(params[key], int):
                try:
                    params[key] = int(params[key])
                except (ValueError, TypeError):
                    # Keep the default if conversion fails
                    pass
        
        # Extract query type from message
        query_type = "general"
        
        # Look for explicit query types
        if "QUERY_TYPE:" in message:
            query_lines = message.split("\n")
            for line in query_lines:
                if line.startswith("QUERY_TYPE:"):
                    query_type = line.replace("QUERY_TYPE:", "").strip().lower()
                    break
        
        # Parse parameters
        if "PARAMS:" in message:
            params_section = message.split("PARAMS:")[1].split("\n\n")[0].strip()
            
            # Parse each parameter line
            param_lines = params_section.split("\n")
            for line in param_lines:
                line = line.strip()
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    # Convert to appropriate types
                    if key == "days" or key == "limit":
                        try:
                            value = int(value)
                        except:
                            pass
                    
                    params[key] = value
        
        # Infer query type from message if not explicitly specified
        if query_type == "general":
            message_lower = message.lower()
            
            # Check for timeframe specifications in the query text and update params
            if '4-hour' in message_lower or '4 hour' in message_lower or '4h' in message_lower:
                params['interval'] = '4h'
                logger.info(f"Detected 4-hour timeframe in message, setting interval to {params['interval']}")
            elif '1-hour' in message_lower or '1 hour' in message_lower or '1h' in message_lower or 'hourly' in message_lower:
                params['interval'] = '1h'
            elif '15-minute' in message_lower or '15 minute' in message_lower or '15m' in message_lower:
                params['interval'] = '15m'
            elif '30-minute' in message_lower or '30 minute' in message_lower or '30m' in message_lower:
                params['interval'] = '30m'
            elif 'daily' in message_lower or 'day' in message_lower:
                params['interval'] = 'D'
                
            # Check for time period specifications
            if '2 weeks' in message_lower or 'two weeks' in message_lower:
                params['days'] = 14
                logger.info(f"Detected 2-week period in message, setting days to {params['days']}")
            elif 'week' in message_lower and not any(term in message_lower for term in ['2 week', 'two week']):
                params['days'] = 7
            elif 'month' in message_lower:
                params['days'] = 30
            elif '3 days' in message_lower or 'three days' in message_lower:
                params['days'] = 3
                
            # Determine query type based on message content
            if any(term in message_lower for term in ["get market data", "market data", "price data", "ohlc", "candles"]):
                query_type = "market_data"
            elif any(term in message_lower for term in ["technical analysis", "analyze", "ta"]):
                query_type = "technical_analysis"
            elif any(term in message_lower for term in ["current price", "latest price", "price"]) and not any(term in message_lower for term in ["history", "historical", "market data"]):
                query_type = "price"
            elif any(term in message_lower for term in ["volatility", "standard deviation", "risk"]):
                query_type = "volatility"
            elif any(term in message_lower for term in ["support", "resistance", "level"]):
                query_type = "support_resistance"
            elif any(term in message_lower for term in ["summary", "overview", "market summary"]):
                query_type = "market_summary"
            elif any(term in message_lower for term in ["available symbols", "list symbols", "symbols"]):
                query_type = "available_symbols"
            elif any(term in message_lower for term in ["available intervals", "list intervals", "intervals"]):
                query_type = "available_intervals"
            elif any(term in message_lower for term in ["help", "commands", "guidance"]):
                query_type = "help"
        
        return query_type, params
    
    def _format_response(self, data: Dict[str, Any], message_type: str, summary: str = "") -> str:
        """
        Format a response message
        
        Args:
            data: Response data
            message_type: Type of message
            summary: Optional summary text
            
        Returns:
            Formatted response message
        """
        # Check for error
        if "error" in data:
            return f"Error: {data['error']}"
        
        # Format based on message type
        if message_type == "market_data":
            return self._format_market_data(data, summary)
        elif message_type == "technical_analysis":
            return self._format_technical_analysis(data, summary)
        elif message_type == "price":
            return self._format_price_data(data, summary)
        elif message_type == "volatility":
            return self._format_volatility(data, summary)
        elif message_type == "support_resistance":
            return self._format_support_resistance(data, summary)
        elif message_type == "market_summary":
            return self._format_market_summary(data, summary)
        elif message_type == "symbols_list":
            return self._format_symbols_list(data, summary)
        elif message_type == "intervals_list":
            return self._format_intervals_list(data, summary)
        else:
            # Fallback formatting - convert dict to JSON string
            return f"{summary}\n\n```json\n{json.dumps(data, indent=2)}\n```"
    
    def _format_market_data(self, data: Dict[str, Any], summary: str = "", format_type: str = "text") -> str:
        """
        Format market data response
        
        Args:
            data: Market data dictionary
            summary: Optional summary text
            format_type: Output format ('json', 'markdown', 'text')
            
        Returns:
            Formatted market data
        """
        # Ensure format_type is a string
        if not isinstance(format_type, str):
            logger.warning(f"format_type is not a string: {type(format_type)}, converting to string")
            format_type = str(format_type)
        
        # Convert to lowercase for comparison
        format_type_lower = format_type.lower()
        
        # For JSON format, just dump the data structure
        if format_type_lower == 'json':
            logger.info("Using JSON format for market data")
            return json.dumps(data, indent=2, default=str)
            
        # For text or markdown formats
        if not summary:
            summary = f"Market Data for {data.get('symbol', 'Unknown')} ({data.get('interval', 'Unknown')})"
        
        if format_type.lower() == 'markdown':
            result = f"### {summary}\n\n"
        else:
            result = f"{summary}\n\n"
        
        if "data" in data and len(data["data"]) > 0:
            result += f"Total Records: {len(data['data'])}\n\n"
            
            # Format sample of the data
            if format_type.lower() == 'markdown':
                result += "#### Sample Data (most recent first)\n\n"
                result += "| Timestamp | Open | High | Low | Close | Volume |\n"
                result += "|-----------|------|------|-----|-------|--------|\n"
                
                # Show up to 5 records
                for i, record in enumerate(data["data"][:5]):
                    # Ensure timestamp is a string and handle different formats
                    timestamp_val = record.get("timestamp", "")
                    if isinstance(timestamp_val, (int, float)):
                        # Convert numeric timestamp to string
                        from datetime import datetime
                        try:
                            timestamp = datetime.fromtimestamp(int(timestamp_val)).strftime("%Y-%m-%d %H:%M:%S")
                        except (ValueError, TypeError, OverflowError):
                            timestamp = f"Unknown ({timestamp_val})"
                    else:
                        # Already a string format
                        timestamp = str(timestamp_val).replace("T", " ")[:19]
                    
                    result += f"| {timestamp} "
                    result += f"| ${float(record.get('open', 0)):.2f} "
                    result += f"| ${float(record.get('high', 0)):.2f} "
                    result += f"| ${float(record.get('low', 0)):.2f} "
                    result += f"| ${float(record.get('close', 0)):.2f} "
                    result += f"| {float(record.get('volume', 0)):.1f} |\n"
            else:
                result += "Sample Data (most recent first):\n```\n"
                result += f"{'Timestamp':<20} {'Open':<10} {'High':<10} {'Low':<10} {'Close':<10} {'Volume':<12}\n"
                
                # Show up to 5 records
                for i, record in enumerate(data["data"][:5]):
                    # Ensure timestamp is a string and handle different formats
                    timestamp_val = record.get("timestamp", "")
                    if isinstance(timestamp_val, (int, float)):
                        # Convert numeric timestamp to string
                        from datetime import datetime
                        try:
                            timestamp = datetime.fromtimestamp(int(timestamp_val)).strftime("%Y-%m-%d %H:%M:%S")
                        except (ValueError, TypeError, OverflowError):
                            timestamp = f"Unknown ({timestamp_val})"
                    else:
                        # Already a string format
                        timestamp = str(timestamp_val).replace("T", " ")[:19]
                        
                    result += f"{timestamp:<20} "
                    result += f"{float(record.get('open', 0)):<10.2f} "
                    result += f"{float(record.get('high', 0)):<10.2f} "
                    result += f"{float(record.get('low', 0)):<10.2f} "
                    result += f"{float(record.get('close', 0)):<10.2f} "
                    result += f"{float(record.get('volume', 0)):<12.2f}\n"
                
                result += "```\n"
            
            # Add note about more data if needed
            if len(data["data"]) > 5:
                result += f"\n(Showing 5 of {len(data['data'])} records)"
        else:
            result += "No market data available."
        
        return result
    
    def _format_technical_analysis(self, data: Dict[str, Any], summary: str = "") -> str:
        """Format technical analysis response"""
        symbol = data.get("symbol", "Unknown")
        interval = data.get("interval", "Unknown")
        
        if not summary:
            summary = f"Technical Analysis for {symbol} ({interval})"
        
        result = f"{summary}\n\n"
        
        # Add market summary
        market_summary = data.get("market_summary", {})
        price_stats = market_summary.get("price_statistics", {})
        trend = market_summary.get("trend", {})
        
        if "latest_price" in market_summary:
            result += f"Current Price: ${market_summary['latest_price']:.2f}\n"
        
        if price_stats:
            result += f"Price Range: ${price_stats.get('min_price', 0):.2f} - ${price_stats.get('max_price', 0):.2f} (Avg: ${price_stats.get('avg_price', 0):.2f})\n"
        
        if trend:
            direction = trend.get("direction", "unknown").replace("_", " ").capitalize()
            strength = trend.get("strength", 0) * 100
            result += f"Trend: {direction} (Strength: {strength:.1f}%)\n"
        
        # Add volatility
        volatility = data.get("volatility", {})
        if "daily_volatility" in volatility:
            result += f"Volatility: Daily {volatility['daily_volatility']*100:.2f}%, Annual {volatility['annualized_volatility']*100:.2f}%\n"
        
        # Add support/resistance levels
        sr_levels = data.get("support_resistance", {})
        if "support_levels" in sr_levels and "resistance_levels" in sr_levels:
            result += "\nKey Levels:\n"
            
            support_levels = sr_levels["support_levels"]
            resistance_levels = sr_levels["resistance_levels"]
            
            result += "Support: " + ", ".join([f"${level:.2f}" for level in support_levels]) + "\n"
            result += "Resistance: " + ", ".join([f"${level:.2f}" for level in resistance_levels]) + "\n"
        
        # Add funding rates if available
        funding = data.get("funding_rates", {})
        if "latest_funding_rate" in funding and "error" not in funding:
            result += f"\nFunding Rate: {funding['latest_funding_rate']*100:.4f}% (Annualized: {funding['annualized_rate']*100:.2f}%)\n"
        
        return result
    
    def _format_price_data(self, data: Dict[str, Any], summary: str = "") -> str:
        """Format price data response"""
        symbol = data.get("symbol", "Unknown")
        
        if not summary:
            summary = f"Price Data for {symbol}"
        
        result = f"{summary}\n\n"
        
        if "price" in data:
            result += f"Latest Price: ${data['price']:.2f}\n"
            result += f"Timestamp: {data.get('timestamp', '').replace('T', ' ')[:19]}"
        else:
            result += "No price data available."
        
        return result
    
    def _format_volatility(self, data: Dict[str, Any], summary: str = "") -> str:
        """Format volatility response"""
        if "data" in data:
            data = data["data"]
        
        symbol = data.get("symbol", "Unknown")
        interval = data.get("interval", "Unknown")
        
        if not summary:
            summary = f"Volatility Analysis for {symbol} ({interval})"
        
        result = f"{summary}\n\n"
        
        if "daily_volatility" in data:
            result += f"Daily Volatility: {data['daily_volatility']*100:.4f}%\n"
            result += f"Annualized Volatility: {data['annualized_volatility']*100:.2f}%\n"
            result += f"Period: {data.get('period_days', 0)} days\n"
            result += f"Data Points: {data.get('data_points', 0)}"
        else:
            result += "No volatility data available."
        
        return result
    
    def _format_support_resistance(self, data: Dict[str, Any], summary: str = "") -> str:
        """Format support/resistance response"""
        if "data" in data:
            data = data["data"]
        
        symbol = data.get("symbol", "Unknown")
        interval = data.get("interval", "Unknown")
        
        if not summary:
            summary = f"Support & Resistance Levels for {symbol} ({interval})"
        
        result = f"{summary}\n\n"
        
        if "current_price" in data:
            result += f"Current Price: ${data['current_price']:.2f}\n\n"
        
        if "support_levels" in data:
            result += "Support Levels:\n"
            for level in data["support_levels"]:
                result += f"- ${level:.2f}\n"
            result += "\n"
        
        if "resistance_levels" in data:
            result += "Resistance Levels:\n"
            for level in data["resistance_levels"]:
                result += f"- ${level:.2f}\n"
        
        return result
    
    def _format_market_summary(self, data: Dict[str, Any], summary: str = "") -> str:
        """Format market summary response"""
        if "data" in data:
            data = data["data"]
        
        # Check for error response
        if "error" in data:
            return f"Error: {data['error']}"
            
        symbol = data.get("symbol", "Unknown")
        interval = data.get("interval", "Unknown")
        
        if not summary:
            summary = f"Market Summary for {symbol} ({interval})"
        
        result = f"{summary}\n\n"
        
        # Add latest price if available
        latest_price = data.get("latest_price")
        if latest_price is not None:
            try:
                result += f"Current Price: ${float(latest_price):.2f}\n"
            except (TypeError, ValueError):
                result += f"Current Price: {latest_price}\n"
        else:
            result += "Current Price: Not available\n"
        
        # Add price statistics
        price_stats = data.get("price_statistics", {}) or {}
        if price_stats and "error" not in price_stats:
            result += "\nPrice Statistics:\n"
            
            # Handle potential missing or None values
            try:
                min_price = price_stats.get("min_price")
                if min_price is not None:
                    result += f"- Min: ${float(min_price):.2f}\n"
            except (TypeError, ValueError):
                pass
                
            try:
                max_price = price_stats.get("max_price")
                if max_price is not None:
                    result += f"- Max: ${float(max_price):.2f}\n"
            except (TypeError, ValueError):
                pass
                
            try:
                avg_price = price_stats.get("avg_price")
                if avg_price is not None:
                    result += f"- Avg: ${float(avg_price):.2f}\n"
            except (TypeError, ValueError):
                pass
                
            try:
                median_price = price_stats.get("median_price")
                if median_price is not None:
                    result += f"- Median: ${float(median_price):.2f}\n"
            except (TypeError, ValueError):
                pass
                
            try:
                period_days = price_stats.get("period_days")
                if period_days is not None:
                    result += f"- Period: {period_days} days\n"
            except (TypeError, ValueError):
                pass
        
        # Add volatility
        volatility = data.get("volatility", {}) or {}
        if volatility and "error" not in volatility:
            result += "\nVolatility:\n"
            
            try:
                daily_vol = volatility.get("daily_volatility")
                if daily_vol is not None:
                    result += f"- Daily: {float(daily_vol)*100:.4f}%\n"
            except (TypeError, ValueError):
                pass
                
            try:
                annual_vol = volatility.get("annualized_volatility")
                if annual_vol is not None:
                    result += f"- Annual: {float(annual_vol)*100:.2f}%\n"
            except (TypeError, ValueError):
                pass
        
        # Add trend information
        trend = data.get("trend", {}) or {}
        if trend:
            result += "\nTrend Analysis:\n"
            try:
                direction = str(trend.get("direction", "unknown")).replace("_", " ").capitalize()
                result += f"- Direction: {direction}\n"
            except Exception:
                pass
                
            try:
                strength = float(trend.get("strength", 0)) * 100
                result += f"- Strength: {strength:.1f}%\n"
            except (TypeError, ValueError):
                pass
            
            try:
                if "price_change_percent" in trend and trend["price_change_percent"] is not None:
                    result += f"- Price Change: {float(trend['price_change_percent']):.2f}%\n"
            except (TypeError, ValueError):
                pass
        
        return result
    
    def _format_symbols_list(self, data: Dict[str, Any], summary: str = "") -> str:
        """Format symbols list response"""
        symbols = data.get("result", [])
        
        if not summary:
            summary = "Available Symbols"
        
        result = f"{summary}\n\n"
        
        if symbols:
            result += f"Total Symbols: {len(symbols)}\n\n"
            result += ", ".join(symbols)
        else:
            result += "No symbols available."
        
        return result
    
    def _format_intervals_list(self, data: Dict[str, Any], summary: str = "") -> str:
        """Format intervals list response"""
        intervals = data.get("result", [])
        symbol = data.get("symbol", "all symbols")
        
        if not summary:
            summary = f"Available Intervals for {symbol}"
        
        result = f"{summary}\n\n"
        
        if intervals:
            result += f"Total Intervals: {len(intervals)}\n\n"
            result += ", ".join(intervals)
        else:
            result += "No intervals available."
        
        return result
    
    def _get_market_data(self, params: Dict[str, Any]) -> str:
        """Get market data"""
        symbol = params.get("symbol", "BTCUSDT")
        interval = params.get("interval", "1h")
        format_type = params.get("format_type", "json")
        
        # Make sure limit is an integer
        try:
            limit_param = params.get("limit", 20)
            if isinstance(limit_param, str):
                limit = int(limit_param)
            elif isinstance(limit_param, (int, float)):
                limit = int(limit_param)
            else:
                limit = 20
        except (TypeError, ValueError):
            limit = 20
            logger.warning(f"Converting limit parameter to integer: {limit}")
        
        try:
            # Determine if we should use days or limit
            if "days" in params and params["days"] is not None:
                try:
                    days_param = params.get("days")
                    if isinstance(days_param, str):
                        days = int(days_param)
                    elif isinstance(days_param, (int, float)):
                        days = int(days_param)
                    else:
                        days = None
                    
                    if days is not None and days > 0:
                        logger.info(f"Using days parameter: {days}")
                        
                        # Calculate start_time from days
                        from datetime import datetime, timedelta
                        start_time = datetime.now() - timedelta(days=days)
                        
                        # Get market data with start_time
                        market_data = self.db_interface.query_manager.get_market_data(
                            symbol=symbol,
                            interval=interval,
                            start_time=start_time,
                            limit=100  # Use a larger limit when using date range
                        )
                    else:
                        # Fall back to limit-based query if days is 0 or None
                        logger.warning(f"Invalid days value: {days}, using limit instead")
                        market_data = self.db_interface.query_manager.get_market_data(
                            symbol=symbol,
                            interval=interval,
                            limit=limit
                        )
                except (TypeError, ValueError) as e:
                    logger.warning(f"Error converting days parameter: {e}, using limit instead")
                    market_data = self.db_interface.query_manager.get_market_data(
                        symbol=symbol,
                        interval=interval,
                        limit=limit
                    )
            else:
                # Use limit-based query
                logger.info(f"Using limit-based query with limit: {limit}")
                market_data = self.db_interface.query_manager.get_market_data(
                    symbol=symbol,
                    interval=interval,
                    limit=limit
                )
            
            if not market_data:
                return f"No market data available for {symbol} with interval {interval}"
            
            # Format the data for display
            response_data = {
                "symbol": symbol,
                "interval": interval,
                "data": market_data
            }
            
            logger.info(f"About to format market data with format_type: {format_type}")
            
            # Debug information
            if not isinstance(format_type, str):
                logger.warning(f"format_type is not a string: {type(format_type)}")
                format_type = str(format_type)
            
            return self._format_market_data(response_data, summary="", format_type=format_type)
        
        except Exception as e:
            import traceback
            stack_trace = traceback.format_exc()
            logger.error(f"Error in market data: {str(e)}\n{stack_trace}")
            return f"Error retrieving market data: {str(e)}"
    
    def _get_technical_analysis(self, params: Dict[str, Any]) -> str:
        """Get technical analysis"""
        symbol = params.get("symbol", "BTCUSDT")
        interval = params.get("interval", "1h")
        
        # Make sure days is an integer
        try:
            days = int(params.get("days", 30))
        except (TypeError, ValueError):
            days = 30
            logger.warning(f"Converting days parameter to integer: {days}")
        
        try:
            logger.info(f"Getting technical analysis for {symbol} ({interval}) over {days} days")
            
            # First check if market data is available
            market_data = self.db_interface.query_manager.get_market_data(
                symbol=symbol,
                interval=interval,
                limit=10
            )
            
            if not market_data:
                return f"No market data available for {symbol} with interval {interval}. Cannot perform technical analysis."
            
            logger.info(f"Retrieved {len(market_data)} market data points")
            
            # Get latest price
            latest_price = self.db_interface.query_manager.get_latest_price(symbol)
            logger.info(f"Latest price: {latest_price}")
            
            # Get volatility
            try:
                volatility = self.db_interface.query_manager.calculate_volatility(
                    symbol=symbol,
                    interval=interval,
                    days=days
                )
                logger.info(f"Retrieved volatility data: {volatility}")
            except Exception as ve:
                logger.error(f"Error calculating volatility: {str(ve)}")
                volatility = {"error": f"Could not calculate volatility: {str(ve)}"}
            
            # Format a simple analysis response
            result = f"Technical Analysis for {symbol} ({interval})\n\n"
            
            if latest_price:
                result += f"Current Price: ${latest_price:.2f}\n\n"
            
            if "error" not in volatility:
                try:
                    daily_vol = volatility.get("daily_volatility", 0) * 100
                    annual_vol = volatility.get("annualized_volatility", 0) * 100
                    result += f"Volatility: {daily_vol:.2f}% daily, {annual_vol:.2f}% annualized\n\n"
                except Exception as vol_err:
                    logger.error(f"Error formatting volatility: {str(vol_err)}")
                    result += f"Volatility: Error calculating\n\n"
            
            result += f"Recent Data (last {len(market_data)} points):\n"
            for i, data in enumerate(market_data[:5]):
                try:
                    timestamp = str(data.get("timestamp", "")).replace("T", " ")[:16]
                    price = float(data.get("close", 0))
                    result += f"{timestamp}: ${price:.2f}\n"
                except Exception as data_err:
                    logger.error(f"Error formatting data point {i}: {str(data_err)}")
                    result += f"Data point {i}: Error formatting\n"
            
            if len(market_data) > 5:
                result += f"... and {len(market_data) - 5} more data points"
            
            return result
        
        except Exception as e:
            logger.error(f"Error in technical analysis: {str(e)}")
            return f"Error performing technical analysis: {str(e)}"
    
    def _get_price_data(self, params: Dict[str, Any]) -> str:
        """Get price data"""
        symbol = params.get("symbol", "BTCUSDT")
        
        try:
            price = self.db_interface.query_manager.get_latest_price(symbol)
            
            return self._format_response({
                "symbol": symbol,
                "price": price,
                "timestamp": params.get("timestamp", "")
            }, "price")
        
        except Exception as e:
            return f"Error retrieving price data: {str(e)}"
    
    def _get_volatility(self, params: Dict[str, Any]) -> str:
        """Get volatility metrics"""
        symbol = params.get("symbol", "BTCUSDT")
        interval = params.get("interval", "1d")
        
        # Make sure days is an integer
        try:
            days = int(params.get("days", 14))
        except (TypeError, ValueError):
            days = 14
            logger.warning(f"Converting days parameter to integer: {days}")
        
        try:
            data = self.db_interface.query_manager.calculate_volatility(
                symbol=symbol,
                interval=interval,
                days=days
            )
            
            return self._format_response({"data": data}, "volatility")
        
        except Exception as e:
            logger.error(f"Error calculating volatility: {str(e)}")
            return f"Error calculating volatility: {str(e)}"
    
    def _get_support_resistance(self, params: Dict[str, Any]) -> str:
        """Get support/resistance levels"""
        symbol = params.get("symbol", "BTCUSDT")
        interval = params.get("interval", "1d")
        
        # Make sure days is an integer
        try:
            days = int(params.get("days", 30))
        except (TypeError, ValueError):
            days = 30
            logger.warning(f"Converting support/resistance days parameter to integer: {days}")
        
        try:
            data = self.db_interface.query_manager.find_support_resistance_levels(
                symbol=symbol,
                interval=interval,
                days=days
            )
            
            return self._format_response({"data": data}, "support_resistance")
        
        except Exception as e:
            logger.error(f"Error finding support/resistance levels: {str(e)}")
            return f"Error finding support/resistance levels: {str(e)}"
    
    def _get_market_summary(self, params: Dict[str, Any]) -> str:
        """Get market summary"""
        symbol = params.get("symbol", "BTCUSDT")
        interval = params.get("interval", "1d")
        
        # Make sure days is an integer
        try:
            days = int(params.get("days", 7))
        except (TypeError, ValueError):
            days = 7
            logger.warning(f"Converting market summary days parameter to integer: {days}")
        
        try:
            data = self.db_interface.query_manager.get_market_summary(
                symbol=symbol,
                interval=interval,
                days=days
            )
            
            return self._format_response({"data": data}, "market_summary")
        
        except Exception as e:
            logger.error(f"Error getting market summary: {str(e)}")
            return f"Error getting market summary: {str(e)}"
    
    def _get_available_symbols(self) -> str:
        """Get available symbols"""
        try:
            symbols = self.db_interface.query_manager.get_available_symbols()
            
            return self._format_response({
                "result": symbols
            }, "symbols_list")
        
        except Exception as e:
            return f"Error retrieving available symbols: {str(e)}"
    
    def _get_available_intervals(self, params: Dict[str, Any]) -> str:
        """Get available intervals"""
        symbol = params.get("symbol")
        
        try:
            intervals = self.db_interface.query_manager.get_available_intervals(symbol)
            
            return self._format_response({
                "symbol": symbol or "all symbols",
                "result": intervals
            }, "intervals_list")
        
        except Exception as e:
            return f"Error retrieving available intervals: {str(e)}"
    
    def _get_help(self) -> str:
        """Get help information"""
        help_text = """
# Database Query Agent Help

This agent provides access to market data and analytics from the database.

## Query Types and Parameters

You can use the following query types:

1. **Market Data**: Get historical price data
   ```
   QUERY_TYPE: market_data
   PARAMS:
   symbol: BTCUSDT
   interval: 1h
   limit: 20
   ```

2. **Technical Analysis**: Get comprehensive technical analysis
   ```
   QUERY_TYPE: technical_analysis
   PARAMS:
   symbol: BTCUSDT
   interval: 1d
   days: 30
   ```

3. **Price Data**: Get latest price
   ```
   QUERY_TYPE: price
   PARAMS:
   symbol: BTCUSDT
   ```

4. **Volatility**: Get volatility metrics
   ```
   QUERY_TYPE: volatility
   PARAMS:
   symbol: BTCUSDT
   interval: 1d
   days: 14
   ```

5. **Support/Resistance**: Get key price levels
   ```
   QUERY_TYPE: support_resistance
   PARAMS:
   symbol: BTCUSDT
   interval: 1d
   days: 30
   ```

6. **Market Summary**: Get market overview
   ```
   QUERY_TYPE: market_summary
   PARAMS:
   symbol: BTCUSDT
   interval: 1d
   days: 7
   ```

7. **Available Symbols**: List available symbols
   ```
   QUERY_TYPE: available_symbols
   ```

8. **Available Intervals**: List available time intervals
   ```
   QUERY_TYPE: available_intervals
   PARAMS:
   symbol: BTCUSDT
   ```

You can also use natural language queries without the formal structure.
"""
        return help_text
    
    def _process_general_query(self, message: str, params: Dict[str, Any]) -> str:
        """Process a general query"""
        try:
            response = self.db_interface.process_query(message, params)
            
            # Determine message type based on query_type
            message_type = response.get("query_type", "general")
            
            if message_type == "available_symbols":
                return self._format_response(response, "symbols_list")
            elif message_type == "available_intervals":
                return self._format_response(response, "intervals_list")
            elif message_type == "latest_price":
                return self._format_response(response, "price")
            elif message_type == "market_summary":
                return self._format_response(response, "market_summary", "Market Summary")
            elif message_type == "volatility":
                return self._format_response(response, "volatility")
            elif message_type == "support_resistance":
                return self._format_response(response, "support_resistance")
            elif message_type == "market_data":
                return self._format_response(response, "market_data")
            elif message_type == "funding_rates":
                if "data" in response:
                    funding_data = response["data"]
                    symbol = funding_data.get("symbol", "Unknown")
                    
                    result = f"Funding Rates for {symbol}\n\n"
                    
                    if "error" in funding_data:
                        result += f"Error: {funding_data['error']}"
                    else:
                        result += f"Latest Rate: {funding_data['latest_funding_rate']*100:.4f}%\n"
                        result += f"Average Rate: {funding_data['average_funding_rate']*100:.4f}%\n"
                        result += f"Annualized Rate: {funding_data['annualized_rate']*100:.2f}%\n"
                        result += f"Period: {funding_data['data_period_days']} days\n"
                        result += f"Events: {funding_data['funding_events']}"
                    
                    return result
                else:
                    return "No funding rate data available."
            else:
                # Generic formatting for unrecognized response types
                return self._format_response(response, "general", "Query Results")
        
        except Exception as e:
            return f"Error processing general query: {str(e)}"
    
    def query_market_data(self, symbol: str, interval: str = '1h', limit: int = 24, 
                         days: Optional[int] = None, format_type: str = 'json') -> str:
        """
        Query market data for a specific symbol.
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            interval: Time interval (e.g., '1m', '5m', '15m', '1h', '4h', '1d')
            limit: Number of data points to retrieve
            days: Number of days to look back (alternative to limit)
            format_type: Output format ('json', 'markdown', 'text')
            
        Returns:
            Formatted market data
        """
        try:
            # Ensure limit is an integer
            try:
                limit = int(limit) if limit is not None else 24
            except (TypeError, ValueError):
                limit = 24
                logger.warning(f"Invalid limit parameter, using default: {limit}")
            
            # Ensure days is an integer if provided
            if days is not None:
                try:
                    days = int(days)
                except (TypeError, ValueError):
                    days = None
                    logger.warning(f"Invalid days parameter, using limit instead")
            
            # Create parameters for the query
            params = {
                "symbol": symbol,
                "interval": interval,
                "limit": limit,
                "days": days,
                "format_type": format_type
            }
            
            # Use the _get_market_data internal method which already handles days vs limit
            return self._get_market_data(params)
            
        except Exception as e:
            logger.error(f"Error in query_market_data: {str(e)}")
            return f"Error retrieving market data: {str(e)}"
    
    def get_market_statistics(self, symbol: str, interval: str = '1d', 
                             days: int = 30, format_type: str = 'json') -> str:
        """
        Get market statistics for a specific symbol.
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            interval: Time interval (e.g., '1h', '4h', '1d')
            days: Number of days to look back
            format_type: Output format ('json', 'markdown', 'text')
            
        Returns:
            Formatted market statistics
        """
        try:
            # Ensure days is an integer
            try:
                days = int(days) if days is not None else 30
            except (TypeError, ValueError):
                days = 30
                logger.warning(f"Invalid days parameter, using default: {days}")
            
            # Create parameters for the query
            params = {
                "symbol": symbol,
                "interval": interval,
                "days": days,
                "format_type": format_type
            }
            
            # Get market summary which includes statistics
            return self._get_market_summary(params)
            
        except Exception as e:
            logger.error(f"Error in get_market_statistics: {str(e)}")
            return f"Error retrieving market statistics: {str(e)}"
    
    def query_funding_rates(self, symbol: str, days: int = 7, format_type: str = 'json') -> str:
        """
        Query funding rates for a specific symbol.
        
        Args:
            symbol: Trading symbol (e.g., 'BTCUSDT')
            days: Number of days to look back
            format_type: Output format ('json', 'markdown', 'text')
            
        Returns:
            Formatted funding rate data
        """
        try:
            # Ensure days is an integer
            try:
                days = int(days) if days is not None else 7
            except (TypeError, ValueError):
                days = 7
                logger.warning(f"Invalid days parameter, using default: {days}")
            
            # Create query message for natural language processing
            query = f"Get funding rates for {symbol} over the past {days} days"
            
            # Process query with natural language understanding
            result = self.db_interface.process_query(query, {
                "symbol": symbol,
                "days": days,
                "format_type": format_type
            })
            
            # If there's an error in the result, return it
            if "error" in result:
                return f"Error retrieving funding rates: {result['error']}"
            
            # Format based on requested format type
            if format_type == 'json':
                return json.dumps(result, indent=2)
            elif format_type == 'markdown':
                return self._format_funding_rates_markdown(result, symbol)
            else: # text format
                return self._format_funding_rates_text(result, symbol)
                
        except Exception as e:
            logger.error(f"Error in query_funding_rates: {str(e)}")
            return f"Error retrieving funding rates: {str(e)}"
    
    def _format_funding_rates_markdown(self, result: Dict[str, Any], symbol: str) -> str:
        """Format funding rates as markdown"""
        response = f"### Funding Rates for {symbol}\n\n"
        
        # Extract funding data from result
        if "data" in result and "funding_rates" in result["data"]:
            funding_data = result["data"]["funding_rates"]
            if funding_data and len(funding_data) > 0:
                response += "| Timestamp | Rate |\n|------------|------|\n"
                for entry in funding_data:
                    timestamp = entry.get("timestamp", "")
                    rate = entry.get("rate", 0)
                    response += f"| {timestamp} | {rate:.6f}% |\n"
            else:
                response += "No funding rate data available."
        else:
            response += "No funding rate data available."
            
        return response
    
    def _format_funding_rates_text(self, result: Dict[str, Any], symbol: str) -> str:
        """Format funding rates as plain text"""
        response = f"Funding Rates for {symbol}:\n\n"
        
        # Extract funding data from result
        if "data" in result and "funding_rates" in result["data"]:
            funding_data = result["data"]["funding_rates"]
            if funding_data and len(funding_data) > 0:
                for entry in funding_data:
                    timestamp = entry.get("timestamp", "")
                    rate = entry.get("rate", 0)
                    response += f"{timestamp}: {rate:.6f}%\n"
            else:
                response += "No funding rate data available."
        else:
            response += "No funding rate data available."
            
        return response
    
    def query_exchange_flows(self, symbol: str, days: int = 7, format_type: str = 'json') -> str:
        """
        Query exchange flows for a specific symbol.
        
        Args:
            symbol: Trading symbol (e.g., 'BTC')
            days: Number of days to look back
            format_type: Output format ('json', 'markdown', 'text')
            
        Returns:
            Formatted exchange flow data
        """
        try:
            # Ensure days is an integer
            try:
                days = int(days) if days is not None else 7
            except (TypeError, ValueError):
                days = 7
                logger.warning(f"Invalid days parameter, using default: {days}")
            
            # Create query message for natural language processing
            query = f"Get exchange flows for {symbol} over the past {days} days"
            
            # Process query with natural language understanding
            result = self.db_interface.process_query(query, {
                "symbol": symbol, 
                "days": days,
                "format_type": format_type
            })
            
            # If there's an error in the result, return it
            if "error" in result:
                return f"Error retrieving exchange flows: {result['error']}"
            
            # Format based on requested format type
            if format_type == 'json':
                return json.dumps(result, indent=2)
            elif format_type == 'markdown':
                return self._format_exchange_flows_markdown(result, symbol)
            else: # text format
                return self._format_exchange_flows_text(result, symbol)
                
        except Exception as e:
            logger.error(f"Error in query_exchange_flows: {str(e)}")
            return f"Error retrieving exchange flows: {str(e)}"
    
    def _format_exchange_flows_markdown(self, result: Dict[str, Any], symbol: str) -> str:
        """Format exchange flows as markdown"""
        response = f"### Exchange Flows for {symbol}\n\n"
        
        # Extract flow data from result
        if "data" in result and "exchange_flows" in result["data"]:
            flow_data = result["data"]["exchange_flows"]
            if flow_data and len(flow_data) > 0:
                response += "| Date | Inflow | Outflow | Net Flow |\n|------|--------|---------|----------|\n"
                for entry in flow_data:
                    date = entry.get("date", "")
                    inflow = entry.get("inflow", 0)
                    outflow = entry.get("outflow", 0)
                    net_flow = entry.get("net_flow", 0)
                    response += f"| {date} | {inflow:.2f} | {outflow:.2f} | {net_flow:.2f} |\n"
            else:
                response += "No exchange flow data available."
        else:
            response += "No exchange flow data available."
            
        return response
    
    def _format_exchange_flows_text(self, result: Dict[str, Any], symbol: str) -> str:
        """Format exchange flows as plain text"""
        response = f"Exchange Flows for {symbol}:\n\n"
        
        # Extract flow data from result
        if "data" in result and "exchange_flows" in result["data"]:
            flow_data = result["data"]["exchange_flows"]
            if flow_data and len(flow_data) > 0:
                for entry in flow_data:
                    date = entry.get("date", "")
                    inflow = entry.get("inflow", 0)
                    outflow = entry.get("outflow", 0)
                    net_flow = entry.get("net_flow", 0)
                    response += f"{date}: Inflow: {inflow:.2f}, Outflow: {outflow:.2f}, Net Flow: {net_flow:.2f}\n"
            else:
                response += "No exchange flow data available."
        else:
            response += "No exchange flow data available."
            
        return response
    
    def close(self) -> None:
        """Close database connections"""
        self.db_interface.close()
        logger.info(f"{self.name} closed database connections")

# Simplified interface for use with AutoGen
def get_database_response(message: str) -> str:
    """
    Get a response from the database query agent
    
    Args:
        message: Query message from another agent
        
    Returns:
        Response from the database query agent
    """
    agent = DatabaseQueryAgent()
    response = agent.process_message(message)
    agent.close()
    return response

# Example usage in a database querying function
def query_database(query_text: str, **params) -> str:
    """
    Query the database with a text query
    
    Args:
        query_text: Query text
        **params: Additional parameters
        
    Returns:
        Query results
    """
    # Format the message
    message = f"{query_text}\n\n"
    
    if params:
        message += "PARAMS:\n"
        for key, value in params.items():
            message += f"{key}: {value}\n"
    
    # Get response from the database query agent
    return get_database_response(message)