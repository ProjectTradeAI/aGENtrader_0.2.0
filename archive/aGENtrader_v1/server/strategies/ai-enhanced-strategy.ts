import { openAIService } from "../services/openai-service";
import { log } from "../vite";
import { TechnicalIndicator, SentimentAnalysis } from "@shared/schema";
import { getServiceStatus } from "../services/llm-service";

interface MarketData {
  symbol: string;
  price: number;
  volume: number;
  timestamp: Date;
}

interface StrategyResult {
  signal: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  reasoning: string;
  metadata: {
    technicalAnalysis: any;
    recommendation: any;
  };
}

export class AIEnhancedStrategy {
  private symbol: string;
  private lastAnalysis: Date | null = null;
  private analysisInterval = 60 * 1000; // 1 minute
  private historicalPrices: number[] = [];
  private readonly maxHistoricalPrices = 100;
  private failureCount = 0;
  private readonly maxFailures = 5;

  constructor(symbol: string) {
    this.symbol = symbol;
  }

  private async checkAgentStatus(): Promise<void> {
    try {
      const llmStatus = await getServiceStatus();
      log('=== AI Trading Agent Status ===', 'ai-strategy');
      log(`Symbol: ${this.symbol}`, 'ai-strategy');
      log('LLM Services:', 'ai-strategy');
      log(`- OpenAI: ${llmStatus.openai.message}`, 'ai-strategy');
      log(`- Fallback: ${llmStatus.activeService === 'basic' ? 'Active' : 'Standby'}`, 'ai-strategy');
      log(`Active Service: ${llmStatus.activeService}`, 'ai-strategy');
      log('Trading Components:', 'ai-strategy');
      log(`- Technical Analysis: Ready`, 'ai-strategy');
      log(`- Trade Execution: Ready`, 'ai-strategy');
      log(`- Risk Management: Active`, 'ai-strategy');
      log('========================', 'ai-strategy');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      log(`Error checking agent status: ${errorMessage}`, 'ai-strategy');
    }
  }

  private updateHistoricalPrices(price: number) {
    this.historicalPrices.push(price);
    if (this.historicalPrices.length > this.maxHistoricalPrices) {
      this.historicalPrices.shift();
    }
  }

  private shouldSkipAnalysis(): boolean {
    if (!this.lastAnalysis) return false;
    const timeSinceLastAnalysis = Date.now() - this.lastAnalysis.getTime();
    return timeSinceLastAnalysis < this.analysisInterval;
  }

  private resetFailureCount() {
    this.failureCount = 0;
  }

  async analyze(
    currentData: MarketData,
    technicalIndicators: TechnicalIndicator[],
    sentimentAnalysis?: SentimentAnalysis | null
  ): Promise<StrategyResult> {
    try {
      await this.checkAgentStatus();

      log(`Starting AI-enhanced analysis for ${this.symbol}`, 'ai-strategy');
      this.updateHistoricalPrices(currentData.price);

      if (this.shouldSkipAnalysis()) {
        return {
          signal: 'HOLD',
          confidence: 50,
          reasoning: 'Skipping analysis - too recent',
          metadata: {
            technicalAnalysis: null,
            recommendation: null
          }
        };
      }

      const formattedIndicators = technicalIndicators.reduce((acc, indicator) => {
        acc[indicator.indicator] = parseFloat(indicator.value);
        return acc;
      }, {} as Record<string, number>);

      let technicalAnalysis;
      try {
        technicalAnalysis = await openAIService.analyzeTechnicalIndicators(this.symbol, formattedIndicators);
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
        log(`Technical analysis failed: ${errorMessage}`, 'ai-strategy');
        technicalAnalysis = { trend: 'neutral', confidence: 50, reasoning: 'Analysis failed' };
      }

      let recommendation;
      try {
        recommendation = await openAIService.generateTradeRecommendation(
          this.symbol,
          technicalAnalysis,
          sentimentAnalysis || undefined,
          currentData.price,
          this.historicalPrices
        );
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
        log(`Trade recommendation failed: ${errorMessage}`, 'ai-strategy');
        this.failureCount++;
        throw error;
      }

      let explanation;
      try {
        explanation = await openAIService.explainTradeDecision(
          recommendation,
          technicalAnalysis,
          sentimentAnalysis || undefined
        );
      } catch (error) {
        explanation = 'Detailed explanation unavailable';
        const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
        log(`Error getting trade explanation: ${errorMessage}`, 'ai-strategy');
      }

      this.lastAnalysis = new Date();
      this.resetFailureCount();

      return {
        signal: recommendation.action,
        confidence: recommendation.confidence,
        reasoning: explanation,
        metadata: {
          technicalAnalysis,
          recommendation
        }
      };
    } catch (error) {
      this.failureCount++;
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      log(`Error in AI-enhanced strategy: ${errorMessage}`, 'ai-strategy');

      if (this.failureCount >= this.maxFailures) {
        log(`Max failures reached for ${this.symbol}, using conservative fallback`, 'ai-strategy');
        return {
          signal: 'HOLD',
          confidence: 30,
          reasoning: 'Multiple analysis failures, using conservative approach',
          metadata: {
            technicalAnalysis: null,
            recommendation: null
          }
        };
      }

      throw error;
    }
  }
}