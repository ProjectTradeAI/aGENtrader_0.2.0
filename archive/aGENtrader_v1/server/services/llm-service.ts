import { log } from '../vite';
import OpenAI from 'openai';
import PQueue from 'p-queue';
import type { ChatCompletion } from 'openai/resources';
import type { SentimentAnalysis } from '@shared/schema';

// Rate limiting queue
const queue = new PQueue({
  interval: 60000,
  intervalCap: 45,
  concurrency: 1
});

// Simple in-memory cache for analysis results
const analysisCache = new Map<string, { result: any; timestamp: number }>();
const CACHE_TTL = 10 * 60 * 1000; // 10 minutes

// Service status tracking
let openAIAvailable = true;

// the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
const MODEL = "gpt-4o";

function isValidChatCompletion(response: any): response is ChatCompletion {
  return response && 
         'choices' in response && 
         Array.isArray(response.choices) && 
         response.choices.length > 0 &&
         response.choices[0].message?.content;
}

async function callOpenAI<T>(prompt: string): Promise<T> {
  const openai = new OpenAI();
  const completion = await openai.chat.completions.create({
    model: MODEL,
    messages: [{ role: "user", content: prompt }],
    response_format: { type: "json_object" }
  });

  if (!completion?.choices?.[0]?.message?.content) {
    throw new Error('Invalid response from OpenAI');
  }

  return JSON.parse(completion.choices[0].message.content) as T;
}

export async function getServiceStatus(): Promise<{
  openai: { available: boolean; message: string };
  activeService: 'openai' | 'basic';
}> {
  try {
    const openai = new OpenAI();
    const testResponse = await openai.chat.completions.create({
      model: MODEL,
      messages: [{ role: "user", content: "test" }],
    });

    openAIAvailable = isValidChatCompletion(testResponse);
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
    log(`OpenAI unavailable: ${errorMessage}`, 'llm');
    openAIAvailable = false;
  }

  return {
    openai: {
      available: openAIAvailable,
      message: openAIAvailable ? 'Connected and ready' : 'Not available'
    },
    activeService: openAIAvailable ? 'openai' : 'basic'
  };
}

interface TechnicalAnalysis {
  trend: string;
  confidence: number;
  reasoning: string;
}

export async function analyzeTechnicalIndicators(data: any): Promise<TechnicalAnalysis> {
  const cacheKey = `tech_${JSON.stringify(data)}`;

  if (analysisCache.has(cacheKey)) {
    const cached = analysisCache.get(cacheKey);
    if (Date.now() - cached!.timestamp < CACHE_TTL) {
      return cached!.result;
    }
    analysisCache.delete(cacheKey);
  }

  try {
    if (!openAIAvailable) {
      log('Using fallback technical analysis', 'llm');
      return fallbackAnalysis(data);
    }

    const prompt = `You are a technical analysis expert. Analyze these technical indicators and provide a JSON response with: trend (bullish/bearish/neutral), confidence (0-100), and detailed reasoning.

Technical Data:
${JSON.stringify(data, null, 2)}

Required JSON format:
{
  "trend": "bullish/bearish/neutral",
  "confidence": number between 0-100,
  "reasoning": "detailed explanation"
}`;

    const analysis = (await queue.add(() => callOpenAI<TechnicalAnalysis>(prompt))) as TechnicalAnalysis;

    const normalizedAnalysis: TechnicalAnalysis = {
      trend: ['bullish', 'bearish', 'neutral'].includes(analysis.trend.toLowerCase())
        ? analysis.trend.toLowerCase()
        : 'neutral',
      confidence: Math.min(100, Math.max(0, Number(analysis.confidence) || 50)),
      reasoning: analysis.reasoning || 'Analysis completed without detailed reasoning'
    };

    analysisCache.set(cacheKey, {
      result: normalizedAnalysis,
      timestamp: Date.now()
    });

    return normalizedAnalysis;
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
    log(`Technical Analysis Error: ${errorMessage}`, 'llm');
    openAIAvailable = false;
    return fallbackAnalysis(data);
  }
}

function fallbackAnalysis(data: any): TechnicalAnalysis {
  const indicators = data || {};
  let bullishSignals = 0;
  let bearishSignals = 0;
  let totalSignals = 0;

  if (indicators.rsi) {
    totalSignals++;
    if (parseFloat(indicators.rsi) < 30) bullishSignals++;
    if (parseFloat(indicators.rsi) > 70) bearishSignals++;
  }

  if (indicators.macd) {
    totalSignals++;
    if (parseFloat(indicators.macd) > 0) bullishSignals++;
    if (parseFloat(indicators.macd) < 0) bearishSignals++;
  }

  if (indicators.volume) {
    totalSignals++;
    const volume = parseFloat(indicators.volume);
    const avgVolume = indicators.average_volume ? parseFloat(indicators.average_volume) : volume;
    if (volume > avgVolume * 1.5) bullishSignals++;
    if (volume < avgVolume * 0.5) bearishSignals++;
  }

  const confidence = totalSignals > 0 ?
    Math.min(100, Math.max(50, (Math.max(bullishSignals, bearishSignals) / totalSignals) * 100)) :
    50;

  let trend = 'neutral';
  if (bullishSignals > bearishSignals) trend = 'bullish';
  if (bearishSignals > bullishSignals) trend = 'bearish';

  return {
    trend,
    confidence,
    reasoning: `Based on ${totalSignals} indicators: ${bullishSignals} bullish and ${bearishSignals} bearish signals`
  };
}

interface TradeRecommendation {
  signal: string;
  confidence: number;
  reason: string;
}

export async function generateTradeRecommendation(
  technicalAnalysis: TechnicalAnalysis,
  sentimentAnalysis: SentimentAnalysis | null,
  price: number,
  symbol: string
): Promise<TradeRecommendation> {
  try {
    const prompt = `Generate a trade recommendation based on:
Symbol: ${symbol}
Current Price: ${price}
Technical Analysis: ${JSON.stringify(technicalAnalysis)}
Sentiment Analysis: ${sentimentAnalysis ? JSON.stringify(sentimentAnalysis) : 'Not available'}

Required JSON format:
{
  "signal": "BUY/SELL/HOLD",
  "confidence": number between 0-100,
  "reason": "detailed explanation"
}`;

    const recommendation = (await queue.add(() => callOpenAI<TradeRecommendation>(prompt))) as TradeRecommendation;

    return {
      signal: ['BUY', 'SELL', 'HOLD'].includes(recommendation.signal.toUpperCase())
        ? recommendation.signal.toUpperCase()
        : 'HOLD',
      confidence: Math.min(100, Math.max(0, Number(recommendation.confidence) || 50)),
      reason: recommendation.reason || 'Recommendation generated without detailed reasoning'
    };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
    log(`Trade Recommendation Error: ${errorMessage}`, 'llm');
    openAIAvailable = false;

    const { trend, confidence } = technicalAnalysis;
    const signal = trend === 'bullish' ? 'BUY' : trend === 'bearish' ? 'SELL' : 'HOLD';
    return {
      signal,
      confidence: Math.max(50, confidence - 10),
      reason: 'Using rule-based approach due to AI service limitations'
    };
  }
}