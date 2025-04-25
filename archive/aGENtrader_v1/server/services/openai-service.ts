import OpenAI from "openai";
import { log } from "../vite";
import pQueue from "p-queue";
import type { ChatCompletion } from "openai/resources";

// the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

// Rate limiting queue
const queue = new pQueue({
  concurrency: 1,
  interval: 1000,
  intervalCap: 3 // Maximum 3 requests per second
});

interface MarketAnalysis {
  trend: string;
  confidence: number;
  reasoning: string;
}

interface SentimentAnalysis {
  sentiment: string;
  score: number;
  keyInsights: string[];
}

interface TradeRecommendation {
  action: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  reasoning: string;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
}

export class OpenAIService {
  private static instance: OpenAIService;
  private retryCount = 3;
  private retryDelay = 1000;

  private constructor() {}

  static getInstance(): OpenAIService {
    if (!OpenAIService.instance) {
      OpenAIService.instance = new OpenAIService();
    }
    return OpenAIService.instance;
  }

  private async retryWithBackoff<T>(operation: () => Promise<T>): Promise<T> {
    let lastError: Error | unknown;

    for (let i = 0; i < this.retryCount; i++) {
      try {
        const result = await queue.add(operation);
        return result as T;
      } catch (error: unknown) {
        lastError = error;
        const typedError = error as { response?: { status?: number } };
        log(`Retry ${i + 1}/${this.retryCount} failed: ${error}`, 'openai');

        if (typedError.response?.status === 429) {
          await new Promise(resolve => setTimeout(resolve, this.retryDelay * Math.pow(2, i)));
        } else {
          throw error;
        }
      }
    }

    throw lastError;
  }

  async analyzeTechnicalIndicators(
    symbol: string,
    indicators: Record<string, number | string>
  ): Promise<MarketAnalysis> {
    try {
      const prompt = `Analyze these technical indicators for ${symbol}:
      ${Object.entries(indicators)
        .map(([key, value]) => `${key}: ${value}`)
        .join('\n')}

      Provide a market analysis in JSON format with the following structure:
      {
        "trend": "bullish/bearish/neutral",
        "confidence": 0-100,
        "reasoning": "detailed explanation"
      }`;

      const response = await this.retryWithBackoff(async () => {
        const completion = await openai.chat.completions.create({
          model: "gpt-4o",
          messages: [{ role: "user", content: prompt }],
          response_format: { type: "json_object" }
        });

        if (!completion?.choices?.[0]?.message?.content) {
          throw new Error('Empty response from OpenAI');
        }

        return JSON.parse(completion.choices[0].message.content) as MarketAnalysis;
      });

      return response;
    } catch (error) {
      log(`Error in analyzeTechnicalIndicators: ${error}`, 'openai');
      return {
        trend: "neutral",
        confidence: 50,
        reasoning: "Analysis unavailable due to technical difficulties"
      };
    }
  }

  async analyzeSentiment(newsAndSocial: string[]): Promise<SentimentAnalysis> {
    try {
      const prompt = `Analyze the market sentiment from these news and social media sources:
      ${newsAndSocial.join('\n')}

      Provide a sentiment analysis in JSON format with:
      {
        "sentiment": "bullish/bearish/neutral",
        "score": 0-100,
        "keyInsights": ["insight1", "insight2", ...]
      }`;

      const response = await this.retryWithBackoff(async () => {
        const completion = await openai.chat.completions.create({
          model: "gpt-4o",
          messages: [{ role: "user", content: prompt }],
          response_format: { type: "json_object" }
        });

        if (!completion?.choices?.[0]?.message?.content) {
          throw new Error('Empty response from OpenAI');
        }

        return JSON.parse(completion.choices[0].message.content) as SentimentAnalysis;
      });

      return response;
    } catch (error) {
      log(`Error in analyzeSentiment: ${error}`, 'openai');
      return {
        sentiment: "neutral",
        score: 50,
        keyInsights: ["Analysis unavailable due to technical difficulties"]
      };
    }
  }

  async generateTradeRecommendation(
    symbol: string,
    technicalAnalysis: MarketAnalysis,
    sentimentAnalysis: SentimentAnalysis | undefined,
    currentPrice: number,
    historicalPrices: number[]
  ): Promise<TradeRecommendation> {
    try {
      const prompt = `Generate a trade recommendation based on:
      Symbol: ${symbol}
      Current Price: ${currentPrice}
      Technical Analysis: ${JSON.stringify(technicalAnalysis)}
      Sentiment Analysis: ${sentimentAnalysis ? JSON.stringify(sentimentAnalysis) : 'Not available'}
      Recent Price History: ${historicalPrices.join(', ')}

      Provide a trade recommendation in JSON format with:
      {
        "action": "BUY/SELL/HOLD",
        "confidence": 0-100,
        "reasoning": "detailed explanation",
        "riskLevel": "LOW/MEDIUM/HIGH"
      }`;

      const response = await this.retryWithBackoff(async () => {
        const completion = await openai.chat.completions.create({
          model: "gpt-4o",
          messages: [{ role: "user", content: prompt }],
          response_format: { type: "json_object" }
        });

        if (!completion?.choices?.[0]?.message?.content) {
          throw new Error('Empty response from OpenAI');
        }

        return JSON.parse(completion.choices[0].message.content) as TradeRecommendation;
      });

      return response;
    } catch (error) {
      log(`Error in generateTradeRecommendation: ${error}`, 'openai');
      return {
        action: "HOLD",
        confidence: 50,
        reasoning: "Trading recommendation unavailable due to technical difficulties",
        riskLevel: "MEDIUM"
      };
    }
  }

  async explainTradeDecision(
    decision: TradeRecommendation,
    technicalAnalysis: MarketAnalysis,
    sentimentAnalysis: SentimentAnalysis | undefined
  ): Promise<string> {
    try {
      const prompt = `Explain this trading decision in detail:
      Decision: ${JSON.stringify(decision)}
      Based on:
      Technical Analysis: ${JSON.stringify(technicalAnalysis)}
      Sentiment Analysis: ${sentimentAnalysis ? JSON.stringify(sentimentAnalysis) : 'Not available'}

      Provide a natural language explanation that a trader would understand.`;

      const response = await this.retryWithBackoff(async () => {
        const completion = await openai.chat.completions.create({
          model: "gpt-4o",
          messages: [{ role: "user", content: prompt }]
        });

        return completion.choices[0].message.content;
      });

      return response ?? "Explanation unavailable due to technical difficulties.";
    } catch (error) {
      log(`Error in explainTradeDecision: ${error}`, 'openai');
      return "Explanation unavailable due to technical difficulties.";
    }
  }
}

export const openAIService = OpenAIService.getInstance();