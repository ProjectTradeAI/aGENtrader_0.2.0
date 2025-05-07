"""
aGENtrader v2 Trading Configuration

This module provides centralized trading configuration settings.
"""

from typing import Dict, Any

def get_trading_config() -> Dict[str, Any]:
    """
    Get the global trading configuration.
    
    Returns:
        Dictionary with trading configuration
    """
    return {
        "default_interval": "1h",
        "risk_level": "medium",
        "position_sizing": {
            "max_position_size_pct": 5.0,
            "max_total_exposure_pct": 50.0
        },
        "trading_pairs": {
            "crypto": ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT"]
        },
        "agent_weights": {
            "technical_analyst": 1.2,
            "sentiment_analyst": 0.8,
            "liquidity_analyst": 1.0,
            "funding_rate_analyst": 0.8,
            "open_interest_analyst": 1.0
        },
        "consensus_thresholds": {
            "minimum_confidence": 65,
            "minimum_agreement": 0.6
        },
        "timeframes": {
            "liquidity_analyst": "15m",
            "technical_analyst": "1h",
            "sentiment_analyst": "4h",
            "funding_rate_analyst": "4h",
            "open_interest_analyst": "4h"
        }
    }