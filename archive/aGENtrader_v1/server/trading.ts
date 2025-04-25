import { storage } from "./storage";
import type { Trade } from "@shared/schema";
import { scrypt, randomBytes } from "crypto";
import { promisify } from "util";
import { AIEnhancedStrategy } from "./strategies/ai-enhanced-strategy";
import { log } from "./vite";

const scryptAsync = promisify(scrypt);

interface AnalysisMetadata {
  technicalAnalysis: any;
  recommendation?: any;
  sentimentAnalysis?: Record<string, any>;
}

interface AnalysisResult {
  signal: string;
  confidence: number;
  reasoning: string;
  metadata: AnalysisMetadata;
}

// Rest of the imports and initial setup remains unchanged
const SYMBOLS = ["BTC"];
const INTERVAL = 30000; // 30 seconds between trades
const DEMO_USER_ID = 1;

// Simulated price data
const PRICE_RANGE = { min: 100, max: 1000 };
export let currentPrices: Record<string, number> = {};

// Initialize mock prices
SYMBOLS.forEach(symbol => {
  currentPrices[symbol] = Math.floor(Math.random() * (PRICE_RANGE.max - PRICE_RANGE.min)) + PRICE_RANGE.min;
});

// Create demo user if it doesn't exist
async function ensureDemoUser() {
  try {
    const demoUser = await storage.getUserByUsername("demo");
    if (!demoUser) {
      const salt = randomBytes(16).toString("hex");
      const buf = (await scryptAsync("demo123", salt, 64)) as Buffer;
      const hashedPassword = `${buf.toString("hex")}.${salt}`;

      await storage.createUser({
        username: "demo",
        password: hashedPassword,
      });
      log("Created demo user", "trading");
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
    log(`Error ensuring demo user: ${errorMessage}`, "error");
  }
}

function updatePrice(symbol: string): number {
  // Simulate price movement with random walk
  const changePercent = (Math.random() - 0.5) * 0.02; // ±1% max change
  const currentPrice = currentPrices[symbol];
  const newPrice = currentPrice * (1 + changePercent);

  // Keep price within reasonable bounds
  currentPrices[symbol] = Math.max(PRICE_RANGE.min, Math.min(PRICE_RANGE.max, newPrice));
  log(`${symbol} price updated: ${currentPrices[symbol].toFixed(2)}`, "trading");
  return currentPrices[symbol];
}

// Mock technical indicators for demonstration
function getMockTechnicalIndicators(symbol: string, price: number) {
  const timestamp = new Date();
  const indicators = [
    {
      symbol,
      id: 1,
      indicator: "RSI",
      value: String(Math.floor(Math.random() * 100)),
      timestamp,
      parameters: { period: 14 }
    },
    {
      symbol,
      id: 2,
      indicator: "MACD",
      value: String((Math.random() * 2 - 1).toFixed(2)),
      timestamp,
      parameters: { fastPeriod: 12, slowPeriod: 26, signalPeriod: 9 }
    },
    {
      symbol,
      id: 3,
      indicator: "MA_50",
      value: String((price * (1 + (Math.random() - 0.5) * 0.1)).toFixed(2)),
      timestamp,
      parameters: { period: 50 }
    }
  ];
  return indicators;
}

// Add rate limiting for trading operations
const tradeLimiter = new Map<string, number>();
const TRADE_COOLDOWN = 60000; // 1 minute cooldown per symbol

export function startTradingBot(onTrade: (trade: Trade) => void) {
  // Ensure demo user exists when bot starts
  ensureDemoUser().catch(error => {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
    log(`Failed to ensure demo user: ${errorMessage}`, "error");
  });

  // Create AI-enhanced strategies for each symbol
  const strategies: Record<string, AIEnhancedStrategy> = {};
  SYMBOLS.forEach(symbol => {
    strategies[symbol] = new AIEnhancedStrategy(symbol);
    log(`Initialized AI-Enhanced Strategy for ${symbol}`, "trading");
  });

  async function executeTrade() {
    for (const symbol of SYMBOLS) {
      try {
        // Check trade cooldown
        const lastTradeTime = tradeLimiter.get(symbol) || 0;
        if (Date.now() - lastTradeTime < TRADE_COOLDOWN) {
          log(`Skipping ${symbol} trade due to cooldown`, "trading");
          continue;
        }

        const currentPrice = updatePrice(symbol);
        const strategy = strategies[symbol];
        const technicalIndicators = getMockTechnicalIndicators(symbol, currentPrice);

        // Get AI-enhanced analysis
        let analysis: AnalysisResult;
        try {
          const result = await strategy.analyze({
            symbol,
            price: currentPrice,
            volume: Math.random() * 1000000,
            timestamp: new Date()
          }, technicalIndicators);

          analysis = result as AnalysisResult;
        } catch (error) {
          // If AI analysis fails, use a simple fallback strategy
          log(`AI analysis failed for ${symbol}, using fallback strategy`, "trading");
          analysis = {
            signal: Math.random() > 0.7 ? (Math.random() > 0.5 ? "buy" : "sell") : "hold",
            confidence: 50,
            reasoning: "Using fallback strategy due to AI analysis failure",
            metadata: {
              technicalAnalysis: "Analysis unavailable"
            }
          };
        }

        log(`${symbol} Analysis Complete:`, "trading");
        log(`- Current price: $${currentPrice.toFixed(2)}`, "trading");
        log(`- Signal: ${analysis.signal.toUpperCase()}`, "trading");
        log(`- Confidence: ${analysis.confidence}%`, "trading");
        log(`- Reasoning: ${analysis.reasoning}`, "trading");

        if (analysis.signal !== "hold") {
          const quantity = Math.floor(Math.random() * 10) + 1;
          const trade = await storage.createTrade(DEMO_USER_ID, {
            symbol,
            type: analysis.signal.toLowerCase(),
            quantity,
            price: Math.floor(currentPrice),
            metadata: {
              confidence: analysis.confidence,
              reasoning: analysis.reasoning,
              technicalAnalysis: analysis.metadata.technicalAnalysis,
              sentimentAnalysis: analysis.metadata.sentimentAnalysis || undefined
            }
          });

          // Update trade limiter
          tradeLimiter.set(symbol, Date.now());

          log(`Executed trade: ${analysis.signal} ${quantity} ${symbol} at $${currentPrice.toFixed(2)}`, "trading");

          // Broadcast trade update with error handling
          try {
            onTrade(trade);
            log(`Broadcasted trade update for ${symbol}`, "trading");
          } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
            log(`Error broadcasting trade update: ${errorMessage}`, "error");
          }
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
        log(`Error executing trade for ${symbol}: ${errorMessage}`, "error");
      }
    }
  }

  // Start trading loop
  const interval = setInterval(executeTrade, INTERVAL);

  // Return cleanup function
  return () => {
    clearInterval(interval);
    log("Trading bot stopped", "trading");
  };
}