"""
Simple Market Analysis Agent

This script creates a market analysis agent that uses database data
without requiring function_call registration.
"""

import os
import sys
import json
import logging
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import AutoGen
try:
    from autogen import AssistantAgent, UserProxyAgent
except ImportError:
    logger.error("Failed to import AutoGen. Make sure it's installed with 'pip install pyautogen'")
    sys.exit(1)

class MarketDataProvider:
    """Provider for market data from the database"""
    
    def __init__(self):
        """Initialize database connection from environment variables"""
        self.conn = None
        try:
            # Get database connection string from environment
            db_url = os.environ.get("DATABASE_URL")
            if not db_url:
                logger.error("DATABASE_URL environment variable not found")
                return
            
            # Connect to the database
            self.conn = psycopg2.connect(db_url)
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            self.conn = None
    
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self.conn is not None
    
    def get_btc_price_data(self) -> Dict[str, Any]:
        """Get Bitcoin price data from the database"""
        if not self.is_connected():
            return {"error": "Database not connected"}
        
        try:
            result = {}
            
            # Get the latest price
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT close, timestamp
                    FROM market_data
                    WHERE symbol = 'BTCUSDT'
                    ORDER BY timestamp DESC
                    LIMIT 1
                """)
                latest = cur.fetchone()
                if latest:
                    result["current_price"] = float(latest[0])
                    result["latest_update"] = latest[1].isoformat()
            
            # Get price history for last week
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT open, high, low, close, volume, timestamp
                    FROM market_data
                    WHERE symbol = 'BTCUSDT' AND interval = '1d'
                    ORDER BY timestamp DESC
                    LIMIT 7
                """)
                columns = [desc[0] for desc in cur.description]
                daily_data = []
                
                for row in cur.fetchall():
                    data_point = {}
                    for i, col in enumerate(columns):
                        if col == 'timestamp':
                            data_point[col] = row[i].strftime('%Y-%m-%d')
                        else:
                            data_point[col] = float(row[i])
                    daily_data.append(data_point)
                
                result["daily_data"] = daily_data
            
            # Calculate volatility
            if "daily_data" in result and len(result["daily_data"]) > 1:
                closes = [d["close"] for d in result["daily_data"]]
                returns = []
                
                for i in range(1, len(closes)):
                    daily_return = (closes[i-1] / closes[i]) - 1
                    returns.append(daily_return)
                
                if returns:
                    mean_return = sum(returns) / len(returns)
                    squared_diff = [(r - mean_return) ** 2 for r in returns]
                    variance = sum(squared_diff) / len(returns)
                    std_dev = variance ** 0.5
                    
                    result["volatility_7d"] = std_dev * 100
            
            # Calculate 24h change
            if "daily_data" in result and len(result["daily_data"]) > 0:
                latest_close = result["current_price"]
                prev_close = result["daily_data"][0]["close"]
                
                if prev_close > 0:
                    result["24h_change_pct"] = ((latest_close - prev_close) / prev_close) * 100
            
            return result
        except Exception as e:
            logger.error(f"Error getting BTC data: {str(e)}")
            return {"error": str(e)}
    
    def get_technical_analysis(self) -> Dict[str, Any]:
        """Get technical analysis for Bitcoin"""
        if not self.is_connected():
            return {"error": "Database not connected"}
        
        try:
            # Get market data for the last 30 days
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT open, high, low, close, volume, timestamp
                    FROM market_data
                    WHERE symbol = 'BTCUSDT' AND interval = '1d'
                    ORDER BY timestamp DESC
                    LIMIT 30
                """)
                columns = [desc[0] for desc in cur.description]
                data = []
                
                for row in cur.fetchall():
                    data_point = {}
                    for i, col in enumerate(columns):
                        if col == 'timestamp':
                            data_point[col] = row[i].strftime('%Y-%m-%d')
                        else:
                            data_point[col] = float(row[i])
                    data.append(data_point)
            
            # Calculate simple moving averages
            if len(data) >= 20:
                # Calculate 7-day SMA
                closes = [d["close"] for d in data]
                sma7 = sum(closes[:7]) / 7
                sma20 = sum(closes[:20]) / 20
                
                # Determine trend direction
                current_price = closes[0]
                price_sma7 = "above" if current_price > sma7 else "below"
                price_sma20 = "above" if current_price > sma20 else "below"
                
                # Determine if golden/death cross
                cross = None
                if sma7 > sma20:
                    cross = "golden cross (bullish)"
                else:
                    cross = "death cross (bearish)"
                
                # Calculate momentum
                momentum_5d = ((closes[0] / closes[5]) - 1) * 100
                momentum_14d = ((closes[0] / closes[14]) - 1) * 100
                
                return {
                    "sma7": sma7,
                    "sma20": sma20,
                    "price_vs_sma7": price_sma7,
                    "price_vs_sma20": price_sma20,
                    "moving_average_cross": cross,
                    "momentum_5d": momentum_5d,
                    "momentum_14d": momentum_14d,
                    "data_points": len(data)
                }
            else:
                return {"error": "Not enough data points for technical analysis"}
        except Exception as e:
            logger.error(f"Error performing technical analysis: {str(e)}")
            return {"error": str(e)}

def main():
    """Run a simple market analysis agent"""
    # Check API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("No OpenAI API key found in environment variables")
        return "Please set the OPENAI_API_KEY environment variable"
    
    # Initialize market data provider
    data_provider = MarketDataProvider()
    if not data_provider.is_connected():
        logger.error("Could not connect to the database")
        return "Database connection failed"
    
    # Get market data
    btc_data = data_provider.get_btc_price_data()
    tech_analysis = data_provider.get_technical_analysis()
    
    # Combine data
    market_information = {
        "price_data": btc_data,
        "technical_analysis": tech_analysis
    }
    
    # Format market data as a markdown string
    market_data_text = "# Bitcoin Market Analysis\n\n"
    
    # Current price and change
    if "current_price" in btc_data:
        market_data_text += f"## Current Price: ${btc_data['current_price']:,.2f}\n\n"
    
    if "24h_change_pct" in btc_data:
        change = btc_data["24h_change_pct"]
        direction = "📈" if change > 0 else "📉"
        market_data_text += f"24h Change: {change:.2f}% {direction}\n\n"
    
    if "volatility_7d" in btc_data:
        market_data_text += f"7-day Volatility: {btc_data['volatility_7d']:.2f}%\n\n"
    
    # Technical analysis
    market_data_text += "## Technical Analysis\n\n"
    
    if "error" not in tech_analysis:
        market_data_text += f"- 7-day SMA: ${tech_analysis['sma7']:,.2f}\n"
        market_data_text += f"- 20-day SMA: ${tech_analysis['sma20']:,.2f}\n"
        market_data_text += f"- Price is {tech_analysis['price_vs_sma7']} 7-day SMA\n"
        market_data_text += f"- Price is {tech_analysis['price_vs_sma20']} 20-day SMA\n"
        market_data_text += f"- Moving averages show {tech_analysis['moving_average_cross']}\n"
        market_data_text += f"- 5-day Momentum: {tech_analysis['momentum_5d']:.2f}%\n"
        market_data_text += f"- 14-day Momentum: {tech_analysis['momentum_14d']:.2f}%\n\n"
    else:
        market_data_text += f"Technical analysis error: {tech_analysis['error']}\n\n"
    
    # Daily price table
    if "daily_data" in btc_data and btc_data["daily_data"]:
        market_data_text += "## Recent Daily Prices\n\n"
        market_data_text += "| Date | Open | High | Low | Close | Volume |\n"
        market_data_text += "|------|------|------|-----|-------|--------|\n"
        
        for day in btc_data["daily_data"]:
            market_data_text += f"| {day['timestamp']} | ${day['open']:,.2f} | ${day['high']:,.2f} | "
            market_data_text += f"${day['low']:,.2f} | ${day['close']:,.2f} | {day['volume']:,.2f} |\n"
    
    # Create the assistant agent
    assistant = AssistantAgent(
        name="CryptoAnalyst",
        system_message="""You are an expert cryptocurrency market analyst. 
        You analyze Bitcoin price data and technical indicators to provide
        market insights and trading recommendations.""",
        llm_config={
            "config_list": [{"model": "gpt-3.5-turbo", "api_key": api_key}],
            "temperature": 0.2,
        }
    )
    
    # Create the user proxy agent (non-interactive, single reply)
    user = UserProxyAgent(
        name="User",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=0
    )
    
    # Format the query
    query = f"""
    Based on the following market data, provide an analysis of Bitcoin's current market position
    and recommend a trading strategy.
    
    {market_data_text}
    
    Please consider:
    1. Price trends and momentum
    2. Technical indicator signals
    3. Volatility and risk assessment
    4. Short-term and mid-term outlook
    5. Appropriate position sizing and risk management
    
    Conclude with a clear trading recommendation (buy, sell, or hold) and justification.
    """
    
    # Response collector
    response_text = ""
    
    # Define a callback function to capture the first response
    def capture_response(recipient, messages, sender, config):
        nonlocal response_text
        if sender.name == "CryptoAnalyst" and messages:
            response_text = messages[-1].get("content", "")
            return True  # Stop conversation after first response
        return False
        
    # Register the callback
    user.register_reply(
        [assistant], 
        capture_response,
        config={"callback_terminated": True}
    )
    
    # Start the conversation with a timeout
    try:
        user.initiate_chat(
            assistant,
            message=query,
            timeout=30  # 30 second timeout
        )
    except TimeoutError:
        logger.warning("Conversation timed out")
    
    # Save the response to a file
    if response_text:
        with open("market_analysis_result.md", "w") as f:
            f.write(response_text)
        logger.info("Analysis result saved to market_analysis_result.md")
    
    return "Analysis completed"

if __name__ == "__main__":
    try:
        result = main()
        logger.info(result)
    except Exception as e:
        logger.error(f"Error: {str(e)}")