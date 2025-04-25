import { Trade } from "@shared/schema";

export interface TradingStrategy {
  analyze(price: number): "buy" | "sell" | "hold";
  getName(): string;
  getDescription(): string;
  getLastDecisionReason(): string;
}

// Base strategy class with common functionality
export abstract class BaseStrategy implements TradingStrategy {
  protected prices: number[] = [];
  protected readonly windowSize: number;
  protected lastDecisionReason: string = "";

  constructor(windowSize: number = 20) {
    this.windowSize = windowSize;
  }

  abstract analyze(price: number): "buy" | "sell" | "hold";
  abstract getName(): string;
  abstract getDescription(): string;

  getLastDecisionReason(): string {
    return this.lastDecisionReason;
  }

  protected addPrice(price: number) {
    this.prices.push(price);
    if (this.prices.length > this.windowSize) {
      this.prices.shift();
    }
  }

  protected calculateSMA(period: number): number {
    const prices = this.prices.slice(-period);
    if (prices.length === 0) return 0;
    return prices.reduce((sum, price) => sum + price, 0) / prices.length;
  }
}

// Simple Moving Average Strategy Implementation
export class SMAStrategy extends BaseStrategy {
  private readonly shortPeriod: number;
  private readonly longPeriod: number;

  constructor(shortPeriod: number = 5, longPeriod: number = 10) {
    super(longPeriod);
    this.shortPeriod = shortPeriod;
    this.longPeriod = longPeriod;
  }

  analyze(currentPrice: number): "buy" | "sell" | "hold" {
    this.addPrice(currentPrice);

    if (this.prices.length < this.longPeriod) {
      this.lastDecisionReason = `Not enough data (${this.prices.length}/${this.longPeriod} periods)`;
      return "hold";
    }

    const shortSMA = this.calculateSMA(this.shortPeriod);
    const longSMA = this.calculateSMA(this.longPeriod);
    const difference = ((shortSMA - longSMA) / longSMA) * 100;

    if (shortSMA > longSMA * 1.01) {
      this.lastDecisionReason = `Buy signal: Short SMA (${shortSMA.toFixed(2)}) is ${difference.toFixed(2)}% above Long SMA (${longSMA.toFixed(2)})`;
      return "buy";
    } else if (shortSMA < longSMA * 0.99) {
      this.lastDecisionReason = `Sell signal: Short SMA (${shortSMA.toFixed(2)}) is ${Math.abs(difference).toFixed(2)}% below Long SMA (${longSMA.toFixed(2)})`;
      return "sell";
    }

    this.lastDecisionReason = `Hold: Price difference (${difference.toFixed(2)}%) within threshold`;
    return "hold";
  }

  getName(): string {
    return "SMA Crossover Strategy";
  }

  getDescription(): string {
    return `Dual SMA crossover strategy (${this.shortPeriod}/${this.longPeriod} periods)`;
  }
}

// Strategy factory to create different strategies
export class StrategyFactory {
  static createStrategy(type: string): TradingStrategy {
    switch (type.toLowerCase()) {
      case "sma":
        return new SMAStrategy();
      default:
        throw new Error(`Unknown strategy type: ${type}`);
    }
  }
}