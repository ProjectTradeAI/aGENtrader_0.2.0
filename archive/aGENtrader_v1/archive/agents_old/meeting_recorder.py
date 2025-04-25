import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MeetingRecorder:
    def __init__(self):
        self.meetings_dir = "data/meetings/summaries"
        self.exec_summaries_dir = "data/meetings/executive_summaries"
        os.makedirs(self.meetings_dir, exist_ok=True)
        os.makedirs(self.exec_summaries_dir, exist_ok=True)

    def record_meeting(self, chat_result: Dict[str, Any], meeting_type: str = "analysis") -> Optional[str]:
        """Record and summarize a meeting"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            logger.info(f"Recording meeting {timestamp}")

            # Extract key points from messages
            market_analysis = None
            trading_decision = None

            if "messages" in chat_result:
                for msg in chat_result["messages"]:
                    content = msg.get("content", "")
                    try:
                        if "{" in content and "}" in content:
                            start_idx = content.find("{")
                            end_idx = content.rfind("}") + 1
                            json_str = content[start_idx:end_idx]
                            data = json.loads(json_str)

                            # Collect latest market analysis and trading decision
                            if "trend" in data:
                                market_analysis = data
                            elif "decision" in data:
                                trading_decision = data.get("decision", {})

                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSON from message: {str(e)}")
                        continue

            # Generate plain text summary
            summary = self._generate_plain_text_summary(market_analysis, trading_decision)

            # Save executive summary in simple format
            exec_summary_file = f"{self.exec_summaries_dir}/executive_summary_{timestamp}.json"
            with open(exec_summary_file, 'w') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "symbol": "BTCUSDT",  # Default symbol for now
                    "summary": summary
                }, f, indent=2)
                logger.info(f"Executive summary saved to {exec_summary_file}")

            # Save full meeting details separately
            summary_file = f"{self.meetings_dir}/meeting_summary_{timestamp}.json"
            with open(summary_file, 'w') as f:
                json.dump({
                    "meeting_id": timestamp,
                    "timestamp": datetime.now().isoformat(),
                    "market_analysis": market_analysis,
                    "trading_decision": trading_decision
                }, f, indent=2)
                logger.info(f"Full meeting summary saved to {summary_file}")

            return summary_file

        except Exception as e:
            logger.error(f"Error recording meeting: {str(e)}")
            return None

    def _generate_plain_text_summary(self, market_analysis: Dict, trading_decision: Dict) -> str:
        """Generate a concise plain text summary from the meeting data"""
        try:
            summary_parts = []

            # Market Analysis Summary
            if market_analysis:
                trend = market_analysis.get("trend", {})
                direction = trend.get("direction", "neutral").upper()
                timeframe = trend.get("timeframe", "short-term")

                summary_parts.append(f"Market Analysis: {direction} trend in {timeframe} timeframe.")

                # Add technical indicators if available
                indicators = market_analysis.get("technical_indicators", {})
                if indicators:
                    ma_signal = indicators.get("moving_averages", {}).get("signal", "neutral")
                    rsi_signal = indicators.get("rsi", {}).get("signal", "neutral")
                    summary_parts.append(f"Technical Indicators: MA={ma_signal}, RSI={rsi_signal}.")

            # Trading Decision Summary
            if trading_decision:
                action = trading_decision.get("action", "HOLD").upper()
                confidence = trading_decision.get("confidence", 0) * 100

                summary_parts.append(f"Trading Decision: {action} with {confidence:.1f}% confidence.")

                # Add risk management details if available
                risk_mgmt = trading_decision.get("risk_management", {})
                if risk_mgmt:
                    stop_loss = risk_mgmt.get("stop_loss", {}).get("price", 0)
                    take_profit = risk_mgmt.get("take_profit", {}).get("price", 0)
                    position_size = risk_mgmt.get("position_size", 0)
                    summary_parts.append(
                        f"Risk Management: Position Size={position_size}%, "
                        f"Stop Loss=${stop_loss}, Take Profit=${take_profit}."
                    )

            if not summary_parts:
                return "No significant updates from this meeting."

            return " ".join(summary_parts)

        except Exception as e:
            logger.error(f"Error generating plain text summary: {str(e)}")
            return "Error generating meeting summary"