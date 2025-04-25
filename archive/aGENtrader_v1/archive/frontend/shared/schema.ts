import { pgTable, text, serial, integer, boolean, timestamp, numeric, json } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const users = pgTable("users", {
  id: serial("id").primaryKey(),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
});

export const trades = pgTable("trades", {
  id: serial("id").primaryKey(),
  userId: integer("user_id").notNull(),
  symbol: text("symbol").notNull(),
  type: text("type").notNull(), // buy/sell
  quantity: integer("quantity").notNull(),
  price: integer("price").notNull(),
  status: text("status").notNull().default('executed'), // pending/executed/cancelled
  timestamp: timestamp("timestamp").notNull().defaultNow(),
  metadata: json("metadata"), // Store AI analysis results
});

export const marketData = pgTable("market_data", {
  id: serial("id").primaryKey(),
  symbol: text("symbol").notNull(),
  interval: text("interval").notNull(), // 1m, 5m, 15m, 30m, 1h, 4h, D
  timestamp: timestamp("timestamp").notNull(),
  open: numeric("open").notNull(),
  high: numeric("high").notNull(),
  low: numeric("low").notNull(),
  close: numeric("close").notNull(),
  volume: numeric("volume").notNull(),
  source: text("source").notNull().default('coinapi'),
  metadata: json("metadata"), // Additional market data fields
}, (table) => ({
  market_data_unique_idx: {
    name: 'market_data_symbol_interval_timestamp_idx',
    columns: [table.symbol, table.interval, table.timestamp],
    unique: true
  }
}));

export const historicalMarketData = pgTable("historical_market_data", {
  id: serial("id").primaryKey(),
  symbol: text("symbol").notNull(),
  timestamp: timestamp("timestamp").notNull(),
  price: numeric("price").notNull(),
  volume: numeric("volume"),
  market_cap: numeric("market_cap"),
  timeframe: text("timeframe").notNull(), // 15m, 1h, 4h, 1d, 1w
}, (table) => ({
  unique_historical_data_point: { columns: [table.timestamp, table.symbol, table.timeframe] }
}));

export const technicalIndicators = pgTable("technical_indicators", {
  id: serial("id").primaryKey(),
  symbol: text("symbol").notNull(),
  indicator: text("indicator").notNull(), // e.g., "sma", "rsi"
  value: numeric("value").notNull(),
  parameters: json("parameters"), // e.g., {"period": 14} for RSI
  timestamp: timestamp("timestamp").notNull(),
});

// Schema for inserting trades with AI metadata
export const insertTradeSchema = createInsertSchema(trades).pick({
  symbol: true,
  type: true,
  quantity: true,
  price: true,
  metadata: true,
}).extend({
  metadata: z.object({
    confidence: z.number().min(0).max(100).optional(),
    reasoning: z.string().optional(),
    technicalAnalysis: z.record(z.any()).optional(),
    sentimentAnalysis: z.record(z.any()).optional(),
  }).optional(),
});

export const insertUserSchema = createInsertSchema(users).pick({
  username: true,
  password: true,
});

export const insertMarketDataSchema = createInsertSchema(marketData).pick({
  symbol: true,
  interval: true,
  timestamp: true,
  open: true,
  high: true,
  low: true,
  close: true,
  volume: true,
  source: true,
  metadata: true,
});

export const insertHistoricalMarketDataSchema = createInsertSchema(historicalMarketData).pick({
  symbol: true,
  timestamp: true,
  price: true,
  volume: true,
  market_cap: true,
  timeframe: true,
});

export const insertTechnicalIndicatorSchema = createInsertSchema(technicalIndicators).pick({
  symbol: true,
  indicator: true,
  value: true,
  parameters: true,
  timestamp: true,
});

// New tables for meetings and summaries
export const meetings = pgTable("meetings", {
  id: serial("id").primaryKey(),
  meeting_id: text("meeting_id").notNull().unique(),
  meeting_type: text("meeting_type").notNull(),
  timestamp: timestamp("timestamp").notNull().defaultNow(),
  participants: json("participants").notNull(),
  discussions: json("discussions").notNull(),
  decisions: json("decisions").notNull(),
  meeting_duration: integer("meeting_duration").notNull(),
  executive_summary: json("executive_summary"),
});

// Zod schemas for validation
export const marketTrendSchema = z.object({
  direction: z.string(),
  strength: z.number(),
  timeframe: z.string(),
});

export const marketOverviewSchema = z.object({
  market_trend: marketTrendSchema,
  key_indicators: z.object({
    moving_averages: z.string(),
    rsi: z.string(),
    volume: z.string(),
  }),
  sentiment: z.string(),
  key_levels: z.object({
    nearest_support: z.number(),
    nearest_resistance: z.number(),
  }),
});

export const tradingRecommendationSchema = z.object({
  action: z.string(),
  confidence: z.number(),
  timeframe: z.string(),
  key_reasons: z.array(z.string()),
  risk_profile: z.object({
    position_size: z.number(),
    stop_loss: z.number(),
    take_profit: z.number(),
  }),
});

export const keyMetricsSchema = z.object({
  participants: z.number(),
  analysis_points: z.number(),
  decisions_made: z.number(),
});

export const executiveSummarySchema = z.object({
  timestamp: z.string(),
  meeting_type: z.string(),
  market_overview: marketOverviewSchema,
  trading_recommendation: tradingRecommendationSchema,
  key_metrics: keyMetricsSchema,
});

export const agentStatementSchema = z.object({
  agent: z.string(),
  content: z.string(),
});

export const decisionSchema = z.object({
  symbol: z.string(),
  signal: z.string(),
  confidence: z.number(),
  strategy: z.string(),
  risk_profile: z.string(),
  reason: z.string(),
  timestamp: z.string(),
  price: z.number(),
});

export const discussionSchema = z.object({
  topic: z.string(),
  symbol: z.string().optional(),
  statements: z.array(agentStatementSchema),
  decision: decisionSchema.nullable(),
});

export const meetingSchema = z.object({
  meeting_id: z.string(),
  timestamp: z.string(),
  meeting_type: z.string(),
  participants: z.array(z.string()),
  discussions: z.array(discussionSchema),
  decisions: z.record(decisionSchema),
  meeting_duration: z.number(),
  executive_summary: executiveSummarySchema.optional(),
});

// Insert schemas
export const insertMeetingSchema = createInsertSchema(meetings).omit({
  id: true,
});

// Add SentimentAnalysis schema and type
export const sentimentAnalysisSchema = z.object({
  sentiment: z.string(),
  confidence: z.number(),
  score: z.number(),
  keyInsights: z.array(z.string()),
  factors: z.array(z.string()).optional(),
  timestamp: z.string().optional(),
});

export type SentimentAnalysis = z.infer<typeof sentimentAnalysisSchema>;

export type InsertUser = z.infer<typeof insertUserSchema>;
export type User = typeof users.$inferSelect;
export type Trade = typeof trades.$inferSelect;
export type InsertTrade = z.infer<typeof insertTradeSchema>;
export type MarketData = typeof marketData.$inferSelect;
export type InsertMarketData = z.infer<typeof insertMarketDataSchema>;
export type HistoricalMarketData = typeof historicalMarketData.$inferSelect;
export type InsertHistoricalMarketData = z.infer<typeof insertHistoricalMarketDataSchema>;
export type TechnicalIndicator = typeof technicalIndicators.$inferSelect;
export type InsertTechnicalIndicator = z.infer<typeof insertTechnicalIndicatorSchema>;
export type Meeting = typeof meetings.$inferSelect;
export type InsertMeeting = z.infer<typeof insertMeetingSchema>;
export type ExecutiveSummary = z.infer<typeof executiveSummarySchema>;
export type Discussion = z.infer<typeof discussionSchema>;
export type Decision = z.infer<typeof decisionSchema>;
export type AgentStatement = z.infer<typeof agentStatementSchema>;

export interface TradingMetrics {
  totalTrades: number;
  profitLoss: number;
  winRate: number;
  portfolio: { symbol: string; quantity: number }[];
}