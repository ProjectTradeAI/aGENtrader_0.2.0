
"""
Sentiment Analysis Agent

Analyzes social media, news, and market sentiment for cryptocurrencies
to provide additional trading signals.
"""

import numpy as np
import json
import os
from datetime import datetime
import re

class SentimentAnalysisAgent:
    def __init__(self, config_path="config/settings.json"):
        """Initialize the Sentiment Analysis Agent"""
        self.name = "Sentiment Analysis Agent"
        self.config = self._load_config(config_path)
        self.sentiment_data = {}
        
    def _load_config(self, config_path):
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Config file not found at {config_path}. Using default settings.")
            return {
                "data_sources": ["twitter", "reddit", "news"],
                "tracked_assets": ["BTC", "ETH", "SOL", "MATIC"],
                "analysis_timeframe": "24h"
            }
    
    def _simulate_sentiment_collection(self, asset, source):
        """
        Simulate collecting sentiment data from various sources
        
        In a real implementation, this would connect to APIs or 
        use web scraping techniques
        """
        # Simulate sentiment scores (0-1 scale, higher is more positive)
        sentiment_score = np.random.beta(5, 3)  # Slightly positive bias
        
        # Simulate volume (number of mentions)
        volume = int(np.random.gamma(5, 100))
        
        # Simulate some key phrases
        positive_phrases = ["bullish", "to the moon", "breaking out", "undervalued"]
        negative_phrases = ["bearish", "crash", "overvalued", "scam"]
        
        # Select phrases based on sentiment
        if sentiment_score > 0.5:
            # More positive phrases
            phrase_count = int(sentiment_score * 10)
            top_phrases = np.random.choice(positive_phrases, min(phrase_count, len(positive_phrases)), replace=False)
            if np.random.random() < 0.3:  # Add some negative for realism
                top_phrases = np.append(top_phrases, np.random.choice(negative_phrases, 1))
        else:
            # More negative phrases
            phrase_count = int((1-sentiment_score) * 10)
            top_phrases = np.random.choice(negative_phrases, min(phrase_count, len(negative_phrases)), replace=False)
            if np.random.random() < 0.3:  # Add some positive for realism
                top_phrases = np.append(top_phrases, np.random.choice(positive_phrases, 1))
                
        return {
            "sentiment_score": round(sentiment_score, 2),
            "volume": volume,
            "top_phrases": list(top_phrases),
            "source": source
        }
    
    def analyze_sentiment(self, asset="BTC"):
        """Analyze sentiment for a specific cryptocurrency"""
        print(f"Analyzing sentiment for {asset}...")
        
        # Collect sentiment from all configured sources
        sentiment_by_source = {
            source: self._simulate_sentiment_collection(asset, source)
            for source in self.config["data_sources"]
        }
        
        # Aggregate sentiment across sources
        aggregate_score = sum(data["sentiment_score"] for data in sentiment_by_source.values()) / len(self.config["data_sources"])
        total_volume = sum(data["volume"] for data in sentiment_by_source.values())
        
        # Determine overall sentiment
        sentiment_label = "neutral"
        if aggregate_score > 0.65:
            sentiment_label = "very positive"
        elif aggregate_score > 0.55:
            sentiment_label = "positive"
        elif aggregate_score < 0.35:
            sentiment_label = "very negative"
        elif aggregate_score < 0.45:
            sentiment_label = "negative"
            
        # Collect all phrases
        all_phrases = []
        for source_data in sentiment_by_source.values():
            all_phrases.extend(source_data["top_phrases"])
        
        # Count phrase occurrences
        phrase_counts = {}
        for phrase in all_phrases:
            if phrase in phrase_counts:
                phrase_counts[phrase] += 1
            else:
                phrase_counts[phrase] = 1
                
        # Sort by count
        trending_phrases = sorted(phrase_counts.items(), key=lambda x: x[1], reverse=True)
        
        result = {
            "asset": asset,
            "aggregate_sentiment": round(aggregate_score, 2),
            "sentiment_label": sentiment_label,
            "total_volume": total_volume,
            "sentiment_by_source": sentiment_by_source,
            "trending_phrases": trending_phrases[:5],
            "timestamp": datetime.now().isoformat()
        }
        
        self.sentiment_data[asset] = result
        self._save_sentiment_data()
        
        return result
    
    def _save_sentiment_data(self):
        """Save sentiment data to file"""
        os.makedirs("data", exist_ok=True)
        with open("data/sentiment_analysis.json", "w") as file:
            json.dump(self.sentiment_data, file, indent=2)
    
    def get_trading_signal(self, asset="BTC"):
        """Convert sentiment analysis into a trading signal"""
        # Get latest sentiment or analyze if not available
        if asset not in self.sentiment_data:
            self.analyze_sentiment(asset)
            
        sentiment_data = self.sentiment_data[asset]
        score = sentiment_data["aggregate_sentiment"]
        
        # Convert to trading signal
        if score > 0.7:
            return {"asset": asset, "signal": "strong_buy", "confidence": round((score - 0.5) * 2, 2)}
        elif score > 0.55:
            return {"asset": asset, "signal": "buy", "confidence": round((score - 0.5) * 2, 2)}
        elif score < 0.3:
            return {"asset": asset, "signal": "strong_sell", "confidence": round((0.5 - score) * 2, 2)}
        elif score < 0.45:
            return {"asset": asset, "signal": "sell", "confidence": round((0.5 - score) * 2, 2)}
        else:
            return {"asset": asset, "signal": "hold", "confidence": 1 - abs(0.5 - score) * 2}

if __name__ == "__main__":
    # Test the agent
    agent = SentimentAnalysisAgent()
    sentiment = agent.analyze_sentiment("ETH")
    print(f"Sentiment analysis: {sentiment}")
    signal = agent.get_trading_signal("ETH")
    print(f"Trading signal: {signal}")
