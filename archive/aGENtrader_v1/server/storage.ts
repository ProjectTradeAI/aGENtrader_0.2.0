import type { User, InsertUser, Trade, InsertTrade, TradingMetrics } from "@shared/schema";
import createMemoryStore from "memorystore";
import session from "express-session";

const MemoryStore = createMemoryStore(session);

export interface IStorage {
  getUser(id: number): Promise<User | undefined>;
  getUserByUsername(username: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;
  createTrade(userId: number, trade: InsertTrade): Promise<Trade>;
  getTradesByUserId(userId: number): Promise<Trade[]>;
  getMetrics(userId: number): Promise<TradingMetrics>;
  sessionStore: session.Store;
}

export class MemStorage implements IStorage {
  private users: Map<number, User>;
  private trades: Map<number, Trade>;
  private currentUserId: number;
  private currentTradeId: number;
  sessionStore: session.Store;

  constructor() {
    this.users = new Map();
    this.trades = new Map();
    this.currentUserId = 1;
    this.currentTradeId = 1;
    this.sessionStore = new MemoryStore({
      checkPeriod: 86400000,
    });
  }

  async getUser(id: number): Promise<User | undefined> {
    return this.users.get(id);
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    return Array.from(this.users.values()).find(
      (user) => user.username === username,
    );
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const id = this.currentUserId++;
    const user = { id, ...insertUser };
    this.users.set(id, user);
    return user;
  }

  async createTrade(userId: number, insertTrade: InsertTrade): Promise<Trade> {
    const id = this.currentTradeId++;
    const trade: Trade = {
      id,
      userId,
      status: "executed",
      timestamp: new Date(),
      ...insertTrade,
      metadata: insertTrade.metadata || {}, // Ensure metadata is always an object
    };
    this.trades.set(id, trade);
    return trade;
  }

  async getTradesByUserId(userId: number): Promise<Trade[]> {
    return Array.from(this.trades.values())
      .filter((trade) => trade.userId === userId)
      .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
  }

  async getMetrics(userId: number): Promise<TradingMetrics> {
    const trades = await this.getTradesByUserId(userId);

    const portfolio = trades.reduce((acc, trade) => {
      const existing = acc.find(p => p.symbol === trade.symbol);
      const quantity = trade.type === "buy" ? trade.quantity : -trade.quantity;

      if (existing) {
        existing.quantity += quantity;
      } else {
        acc.push({ symbol: trade.symbol, quantity });
      }

      return acc;
    }, [] as { symbol: string; quantity: number }[]);

    const profitLoss = trades.reduce((sum, trade) => {
      return sum + (trade.type === "sell" ? trade.price : -trade.price);
    }, 0);

    const wins = trades.filter(t => t.type === "sell" && t.price > 0).length;

    return {
      totalTrades: trades.length,
      profitLoss,
      winRate: trades.length ? (wins / trades.length) * 100 : 0,
      portfolio,
    };
  }
}

export const storage = new MemStorage();